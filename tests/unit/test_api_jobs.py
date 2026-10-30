"""Tests of babylon_api.jobs and of the operation routes (fake Kubernetes, see conftest.py)."""

import json

import pytest
from kubernetes import client

from babylon_api.jobs import (
    LABEL_OPERATION_ID,
    ApiConfigurationError,
    JobSettings,
    build_job,
    job_status,
)
from babylon_api.schemas import ApplyRequest

SETTINGS = JobSettings(namespace="babylon", image="babylon:test", service_account="babylon-worker", secret_name="babylon-worker")

APPLY = {
    "repository": {"url": "https://github.com/acme/deployments", "ref": "v1.2"},
    "deploy_dir": "projects/brewery",
    "context": "dev",
    "tenant": "tenant-a",
}


# build_job: the manifest

@pytest.fixture
def job() -> client.V1Job:
    return build_job("apply", ApplyRequest(**APPLY), "0123456789ab", SETTINGS)


def test_job_identity_and_labels(job):
    assert job.metadata.name == "babylon-apply-0123456789ab"
    assert job.metadata.namespace == "babylon"
    labels = job.metadata.labels
    assert labels[LABEL_OPERATION_ID] == "0123456789ab"
    assert labels["babylon.cosmotech.com/tenant"] == "tenant-a"
    assert job.spec.template.metadata.labels == labels  # pods findable by operation id


def test_job_runs_the_worker_with_the_request(job):
    container = job.spec.template.spec.containers[0]
    assert container.command == ["python", "-m", "babylon_api.worker"]
    env = {e.name: e.value for e in container.env}
    payload = json.loads(env["BABYLON_OPERATION"])
    assert payload["operation"] == "apply"
    assert payload["request"]["repository"]["ref"] == "v1.2"
    assert payload["request"]["variable_files"] == ["variables.yaml"]  # defaults are filled
    assert env["BABYLON_K8S_AUTH"] == "incluster"
    assert container.env_from[0].secret_ref.name == "babylon-worker"


def test_job_has_no_retry_a_deadline_and_a_ttl(job):
    assert job.spec.backoff_limit == 0
    assert job.spec.active_deadline_seconds == 3600
    assert job.spec.ttl_seconds_after_finished == 86400
    assert job.spec.template.spec.restart_policy == "Never"
    assert job.spec.template.spec.service_account_name == "babylon-worker"


def test_job_is_locked_down(job):
    sc = job.spec.template.spec.containers[0].security_context
    assert sc.run_as_non_root and sc.read_only_root_filesystem and not sc.allow_privilege_escalation
    assert sc.capabilities.drop == ["ALL"]


def test_no_secret_means_no_env_from():
    settings = JobSettings(namespace="babylon", image="i", service_account="sa")
    job = build_job("apply", ApplyRequest(**APPLY), "0123456789ab", settings)
    assert job.spec.template.spec.containers[0].env_from is None
    assert job.spec.template.spec.image_pull_secrets is None


def test_pull_secret_is_passed_to_the_worker_pod():
    env = {"BABYLON_API_NAMESPACE": "ns", "BABYLON_WORKER_IMAGE": "img:1", "BABYLON_WORKER_PULL_SECRET": "registry-auth"}
    job = build_job("apply", ApplyRequest(**APPLY), "0123456789ab", JobSettings.from_env(env))
    assert [s.name for s in job.spec.template.spec.image_pull_secrets] == ["registry-auth"]


def test_settings_from_env():
    s = JobSettings.from_env({"BABYLON_API_NAMESPACE": "ns", "BABYLON_WORKER_IMAGE": "img:1"})
    assert (s.namespace, s.image, s.service_account, s.secret_name) == ("ns", "img:1", "babylon-worker", None)
    with pytest.raises(ApiConfigurationError, match="BABYLON_WORKER_IMAGE"):
        JobSettings.from_env({"BABYLON_API_NAMESPACE": "ns"})


# job_status

def status(**fields) -> client.V1Job:
    conditions = fields.pop("conditions", None)
    conds = [client.V1JobCondition(type=t, status="True") for t in conditions or []]
    return client.V1Job(status=client.V1JobStatus(conditions=conds or None, **fields))


@pytest.mark.parametrize(
    "job, expected",
    [
        (client.V1Job(), "pending"),
        (status(), "pending"),
        (status(active=1), "running"),
        (status(succeeded=1), "succeeded"),
        (status(failed=1), "failed"),
        (status(active=1, conditions=["Failed"]), "failed"),  # deadline exceeded: still "active" for a moment
        (status(conditions=["Complete"]), "succeeded"),
    ],
)
def test_job_status(job, expected):
    assert job_status(job) == expected


# routes

def test_apply_creates_one_job_and_returns_202(api, fake_kube):
    res = api.post("/apply", json=APPLY)
    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "pending"
    assert fake_kube.batch.jobs[0].metadata.name == body["job_name"] == f"babylon-apply-{body['operation_id']}"


def test_operation_lifecycle(api, fake_kube):
    op_id = api.post("/apply", json=APPLY).json()["operation_id"]
    assert api.get(f"/operations/{op_id}").json()["status"] == "pending"

    job = fake_kube.batch.jobs[0]
    job.status = client.V1JobStatus(active=1)
    assert api.get(f"/operations/{op_id}").json()["status"] == "running"

    # The worker finished and wrote its summary in the termination message.
    job.status = client.V1JobStatus(failed=1)
    summary = {"status": "failed", "commit": "abc", "resources": [{"resource": "solution", "status": "failed"}]}
    terminated = client.V1ContainerStateTerminated(exit_code=1, message=json.dumps(summary))
    fake_kube.core.pods.append(
        client.V1Pod(
            metadata=client.V1ObjectMeta(labels={LABEL_OPERATION_ID: op_id}),
            status=client.V1PodStatus(
                container_statuses=[
                    client.V1ContainerStatus(
                        name="worker",
                        image="i",
                        image_id="",
                        ready=False,
                        restart_count=0,
                        state=client.V1ContainerState(terminated=terminated),
                    )
                ]
            ),
        )
    )
    body = api.get(f"/operations/{op_id}").json()
    assert (body["status"], body["tenant"], body["operation"]) == ("failed", "tenant-a", "apply")
    assert body["result"] == summary


def test_unknown_operation_is_404(api):
    assert api.get("/operations/0123456789ab").status_code == 404


@pytest.mark.parametrize("bad_id", ["ABC", "0123456789abc", "../../etc", "x" * 12])
def test_operation_id_format_is_checked(api, bad_id):
    assert api.get(f"/operations/{bad_id}").status_code in (404, 422)


def test_kubernetes_refusal_is_a_502(api, fake_kube):
    def forbidden(namespace, body):
        raise client.exceptions.ApiException(status=403, reason="Forbidden")

    fake_kube.batch.create_namespaced_job = forbidden
    res = api.post("/apply", json=APPLY)
    assert res.status_code == 502
    assert "403 Forbidden" in res.json()["detail"]


def test_missing_configuration_is_a_503(fake_kube, monkeypatch):
    from fastapi.testclient import TestClient

    from babylon_api.app import app, get_settings

    del app.dependency_overrides[get_settings]  # real settings, from an empty environment
    monkeypatch.delenv("BABYLON_API_NAMESPACE", raising=False)
    res = TestClient(app).post("/apply", json=APPLY)
    assert res.status_code == 503
    assert "BABYLON_API_NAMESPACE" in res.json()["detail"]
