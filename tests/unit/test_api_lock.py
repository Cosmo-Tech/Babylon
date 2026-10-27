"""Tests of the tenant lock Lease logic, worker wiring and API 409. No cluster needed.

FakeCoordination reproduces the two Kubernetes guarantees the lock relies on:
- create of an existing name -> 409
- replace/delete with a stale resourceVersion -> 409
"""

import copy
import json
from datetime import datetime, timedelta, timezone

import pytest
from kubernetes import client
from kubernetes.client.exceptions import ApiException

from Babylon.core.errors import OperationInProgressError
from babylon_api import lock, worker
from babylon_api.jobs import LABEL_OPERATION_ID, find_active_operation
from babylon_api.lock import acquire, lease_name, release, tenant_lock

NS = "babylon"
NAME = lease_name("dev", "tenant-a")


class FakeCoordination:
    def __init__(self):
        self.leases: dict[str, client.V1Lease] = {}
        self.version = 0

    def _bump(self, lease):
        self.version += 1
        lease.metadata.resource_version = str(self.version)

    def create_namespaced_lease(self, namespace, body):
        if body.metadata.name in self.leases:
            raise ApiException(status=409, reason="AlreadyExists")
        body = copy.deepcopy(body)
        self._bump(body)
        self.leases[body.metadata.name] = body
        return body

    def read_namespaced_lease(self, name, namespace):
        if name not in self.leases:
            raise ApiException(status=404, reason="NotFound")
        return copy.deepcopy(self.leases[name])

    def replace_namespaced_lease(self, name, namespace, body):
        if self.leases[name].metadata.resource_version != body.metadata.resource_version:
            raise ApiException(status=409, reason="Conflict")
        body = copy.deepcopy(body)
        self._bump(body)
        self.leases[name] = body
        return body

    def delete_namespaced_lease(self, name, namespace, body=None):
        if name not in self.leases:
            raise ApiException(status=404, reason="NotFound")
        expected = body.preconditions.resource_version if body and body.preconditions else None
        if expected and self.leases[name].metadata.resource_version != expected:
            raise ApiException(status=409, reason="Conflict")
        del self.leases[name]

    def holder(self, name=NAME):
        lease = self.leases.get(name)
        return lease.spec.holder_identity if lease else None


@pytest.fixture
def coord():
    return FakeCoordination()


def age(coord, seconds):
    """Pretend the current lease was renewed `seconds` ago."""
    coord.leases[NAME].spec.renew_time = datetime.now(timezone.utc) - timedelta(seconds=seconds)


# Lease logic


def test_first_operation_takes_the_lock(coord):
    acquire(coord, NS, NAME, "op1", 60)
    assert coord.holder() == "op1"


def test_second_operation_is_refused_while_held(coord):
    acquire(coord, NS, NAME, "op1", 60)
    with pytest.raises(OperationInProgressError, match="op1"):
        acquire(coord, NS, NAME, "op2", 60)
    assert coord.holder() == "op1"


def test_same_holder_can_acquire_again(coord):
    acquire(coord, NS, NAME, "op1", 60)
    acquire(coord, NS, NAME, "op1", 60)  # no error
    assert coord.holder() == "op1"


def test_expired_lock_is_taken_over(coord):
    acquire(coord, NS, NAME, "op1", 60)
    age(coord, 61)  # op1 was killed without releasing
    acquire(coord, NS, NAME, "op2", 60)
    assert coord.holder() == "op2"


def test_other_tenants_are_independent(coord):
    acquire(coord, NS, lease_name("dev", "tenant-a"), "op1", 60)
    acquire(coord, NS, lease_name("dev", "tenant-b"), "op2", 60)
    acquire(coord, NS, lease_name("prod", "tenant-a"), "op3", 60)
    assert len(coord.leases) == 3


def test_race_on_takeover_is_refused(coord, monkeypatch):
    """Two workers read the same expired Lease; the second replace is refused by resourceVersion."""
    acquire(coord, NS, NAME, "op1", 60)
    age(coord, 61)
    stale = coord.read_namespaced_lease(NAME, NS)  # what op3 read before op2 wrote
    acquire(coord, NS, NAME, "op2", 60)
    monkeypatch.setattr(coord, "read_namespaced_lease", lambda name, ns: copy.deepcopy(stale))
    with pytest.raises(OperationInProgressError, match="same time"):
        acquire(coord, NS, NAME, "op3", 60)
    assert coord.holder() == "op2"


def test_release_only_deletes_our_own_lock(coord):
    acquire(coord, NS, NAME, "op1", 60)
    release(coord, NS, NAME, "op2")  # not ours: kept
    assert coord.holder() == "op1"
    release(coord, NS, NAME, "op1")
    assert NAME not in coord.leases
    release(coord, NS, NAME, "op1")  # already gone: no error


def test_context_manager_releases_even_on_error(coord):
    with pytest.raises(RuntimeError):
        with tenant_lock(coord, NS, "dev", "tenant-a", "op1", 60):
            assert coord.holder() == "op1"
            raise RuntimeError("deploy failed")
    assert NAME not in coord.leases


def test_kubernetes_error_other_than_conflict_is_not_hidden(coord, monkeypatch):
    def forbidden(namespace, body):
        raise ApiException(status=403, reason="Forbidden")

    monkeypatch.setattr(coord, "create_namespaced_lease", forbidden)
    with pytest.raises(ApiException):
        acquire(coord, NS, NAME, "op1", 60)


# worker wiring

APPLY = {"repository": {"url": "https://github.com/acme/d"}, "deploy_dir": "p", "context": "dev", "tenant": "tenant-a"}


def test_worker_runs_inside_the_lock(coord, tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(worker, "_execute", lambda *a: seen.append(coord.holder()) or {"status": "succeeded"})
    factory = lambda c, t: tenant_lock(coord, NS, c, t, "op1", 60)  # noqa: E731
    worker.run({"operation": "apply", "request": APPLY}, tmp_path, lock=factory)
    assert seen == ["op1"]  # held during the operation
    assert NAME not in coord.leases  # released after


def test_worker_refused_when_tenant_is_locked(coord, tmp_path, monkeypatch):
    acquire(coord, NS, NAME, "other-op", 60)
    monkeypatch.setattr(worker, "_execute", lambda *a: pytest.fail("must not run"))
    factory = lambda c, t: tenant_lock(coord, NS, c, t, "op1", 60)  # noqa: E731
    with pytest.raises(OperationInProgressError):
        worker.run({"operation": "apply", "request": APPLY}, tmp_path, lock=factory)
    assert coord.holder() == "other-op"  # untouched


def test_main_reports_lock_refusal_as_failed(coord, tmp_path, monkeypatch):
    acquire(coord, NS, NAME, "other-op", 60)
    monkeypatch.setattr(worker, "lock_from_env", lambda env: lambda c, t: tenant_lock(coord, NS, c, t, "op1", 60))
    result_file = tmp_path / "result"
    code = worker.main(
        {worker.OPERATION_ENV: json.dumps({"operation": "apply", "request": APPLY}), worker.RESULT_PATH_ENV: str(result_file)}
    )
    assert code == 1
    assert "already running" in json.loads(result_file.read_text())["error"]


def test_lock_is_disabled_outside_a_job():
    assert worker.lock_from_env({}) is None
    assert worker.lock_from_env({worker.LOCK_NAMESPACE_ENV: NS, worker.OPERATION_ID_ENV: "op1"}) is not None


def test_job_gives_the_worker_its_lock_settings(fake_kube, api):
    res = api.post("/apply", json=APPLY)
    env = {e.name: e.value for e in fake_kube.batch.jobs[0].spec.template.spec.containers[0].env}
    assert env["BABYLON_OPERATION_ID"] == res.json()["operation_id"]
    assert env["BABYLON_LOCK_NAMESPACE"] == "babylon"
    assert int(env["BABYLON_LOCK_DURATION"]) > fake_kube.batch.jobs[0].spec.active_deadline_seconds


# API: fast 409


def finish(job, condition="Complete"):
    job.status = client.V1JobStatus(conditions=[client.V1JobCondition(type=condition, status="True")])


def test_api_answers_409_while_an_operation_runs_on_the_tenant(api, fake_kube):
    first = api.post("/apply", json=APPLY)
    assert first.status_code == 202
    second = api.post("/destroy", json={**{k: v for k, v in APPLY.items() if k != "deploy_dir"}, "confirm": True})
    assert second.status_code == 409
    assert first.json()["operation_id"] in second.json()["detail"]
    assert len(fake_kube.batch.jobs) == 1


def test_api_accepts_another_tenant_or_after_the_end(api, fake_kube):
    assert api.post("/apply", json=APPLY).status_code == 202
    assert api.post("/apply", json={**APPLY, "tenant": "tenant-b"}).status_code == 202  # other tenant
    assert api.post("/apply", json={**APPLY, "context": "prod"}).status_code == 202  # other context
    finish(fake_kube.batch.jobs[0], "Failed")
    assert api.post("/apply", json=APPLY).status_code == 202  # first one is over


def test_find_active_operation_ignores_finished_jobs(api, fake_kube):
    api.post("/apply", json=APPLY)
    job = fake_kube.batch.jobs[0]
    assert find_active_operation(fake_kube.batch, "babylon", "dev", "tenant-a") == job.metadata.labels[LABEL_OPERATION_ID]
    finish(job)
    assert find_active_operation(fake_kube.batch, "babylon", "dev", "tenant-a") is None


def test_lease_name():
    assert lock.lease_name("dev", "tenant-a") == "babylon-lock-dev-tenant-a"
