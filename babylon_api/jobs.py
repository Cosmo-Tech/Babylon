"""One Kubernetes Job per operation: build it, submit it, read its status back.

Why a Job and not a thread in the API pod?
- isolation: one process per operation, so the `Environment` singleton is never shared;
- an API restart does not kill a running deployment;
- logs, retries, timeout and cleanup are handled by Kubernetes (kubectl logs job/...).

The Job itself is the record of the operation: no database. Its labels carry the
operation id, and the worker writes its result in the container termination message.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Mapping
from dataclasses import dataclass

from kubernetes import client
from pydantic import BaseModel

from Babylon.core.errors import BabylonError

LABEL_MANAGED_BY = "app.kubernetes.io/managed-by"
MANAGED_BY = "babylon-api"
LABEL_OPERATION_ID = "babylon.cosmotech.com/operation-id"
LABEL_OPERATION = "babylon.cosmotech.com/operation"
LABEL_CONTEXT = "babylon.cosmotech.com/context"
LABEL_TENANT = "babylon.cosmotech.com/tenant"

WORK_DIR = "/work"


class ApiConfigurationError(BabylonError):
    """The API itself is not configured (missing environment variable)."""


@dataclass(frozen=True)
class JobSettings:
    """Where and how Jobs are created. Read from the API pod environment."""

    namespace: str  # namespace of the Jobs (the API namespace)
    image: str  # same image as the API: it contains Babylon + babylon_api
    service_account: str  # identity of the worker (RBAC: Secrets/Jobs/... in tenant namespaces)
    secret_name: str | None = None  # optional Secret exposed as env (git token, API_URL, KEYCLOAK_*...)
    active_deadline_seconds: int = 3600  # a stuck operation is killed after 1 hour
    ttl_seconds_after_finished: int = 86400  # Kubernetes deletes the Job (and its status) after 1 day

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> JobSettings:
        environ = os.environ if environ is None else environ
        missing = [v for v in ("BABYLON_API_NAMESPACE", "BABYLON_WORKER_IMAGE") if not environ.get(v)]
        if missing:
            raise ApiConfigurationError(f"Missing configuration: {', '.join(missing)}")
        return cls(
            namespace=environ["BABYLON_API_NAMESPACE"],
            image=environ["BABYLON_WORKER_IMAGE"],
            service_account=environ.get("BABYLON_WORKER_SERVICE_ACCOUNT") or "babylon-worker",
            secret_name=environ.get("BABYLON_WORKER_SECRET") or None,
        )


def new_operation_id() -> str:
    return uuid.uuid4().hex[:12]


def build_job(operation: str, request: BaseModel, operation_id: str, settings: JobSettings) -> client.V1Job:
    """The Job manifest (pure function: no API call, easy to test and to read)."""
    labels = {
        LABEL_MANAGED_BY: MANAGED_BY,
        LABEL_OPERATION_ID: operation_id,
        LABEL_OPERATION: operation,
        LABEL_CONTEXT: request.context,
        LABEL_TENANT: request.tenant,
    }
    payload = json.dumps({"operation": operation, "request": request.model_dump(mode="json")})
    env = [
        client.V1EnvVar(name="BABYLON_OPERATION", value=payload),
        client.V1EnvVar(name="BABYLON_K8S_AUTH", value="incluster"),
        client.V1EnvVar(name="HOME", value=WORK_DIR),  # git and Babylon write under $HOME
    ]
    env_from = None
    if settings.secret_name:
        env_from = [client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name=settings.secret_name))]

    container = client.V1Container(
        name="worker",
        image=settings.image,
        command=["python", "-m", "babylon_api.worker"],
        env=env,
        env_from=env_from,
        working_dir=WORK_DIR,
        termination_message_policy="File",  # the worker writes its JSON result in /dev/termination-log
        volume_mounts=[
            client.V1VolumeMount(name="work", mount_path=WORK_DIR),
            client.V1VolumeMount(name="tmp", mount_path="/tmp"),
        ],
        security_context=client.V1SecurityContext(
            allow_privilege_escalation=False,
            read_only_root_filesystem=True,  # only /work and /tmp are writable
            run_as_non_root=True,
            capabilities=client.V1Capabilities(drop=["ALL"]),
        ),
        resources=client.V1ResourceRequirements(
            requests={"cpu": "100m", "memory": "256Mi"},
            limits={"memory": "1Gi"},
        ),
    )
    pod = client.V1PodSpec(
        restart_policy="Never",
        service_account_name=settings.service_account,
        containers=[container],
        volumes=[
            client.V1Volume(name="work", empty_dir=client.V1EmptyDirVolumeSource()),
            client.V1Volume(name="tmp", empty_dir=client.V1EmptyDirVolumeSource()),
        ],
        security_context=client.V1PodSecurityContext(
            run_as_non_root=True,
            seccomp_profile=client.V1SeccompProfile(type="RuntimeDefault"),
        ),
    )
    return client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=f"babylon-{operation}-{operation_id}", namespace=settings.namespace, labels=labels),
        spec=client.V1JobSpec(
            # No automatic retry: re-running a half-done destroy/apply must be a human decision.
            backoff_limit=0,
            active_deadline_seconds=settings.active_deadline_seconds,
            ttl_seconds_after_finished=settings.ttl_seconds_after_finished,
            template=client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels=labels), spec=pod),
        ),
    )


def job_status(job: client.V1Job) -> str:
    """pending (pod not started) -> running -> succeeded | failed."""
    status = job.status or client.V1JobStatus()
    for condition in status.conditions or []:
        if condition.status == "True" and condition.type in ("Complete", "Failed"):
            return "succeeded" if condition.type == "Complete" else "failed"
    if status.succeeded:
        return "succeeded"
    if status.failed:
        return "failed"
    if status.active:
        return "running"
    return "pending"


def _worker_result(core_api: client.CoreV1Api, namespace: str, operation_id: str) -> dict | None:
    """The JSON summary written by the worker in its termination message, if any."""
    pods = core_api.list_namespaced_pod(namespace, label_selector=f"{LABEL_OPERATION_ID}={operation_id}").items
    for pod in pods:
        for container in (pod.status and pod.status.container_statuses) or []:
            terminated = container.state and container.state.terminated
            if terminated and terminated.message:
                try:
                    return json.loads(terminated.message)
                except ValueError:
                    return {"error": terminated.message}
    return None


def get_operation(batch_api: client.BatchV1Api, core_api: client.CoreV1Api, namespace: str, operation_id: str) -> dict | None:
    """Status of an operation, read from its Job. None if unknown (or already cleaned up by the TTL)."""
    jobs = batch_api.list_namespaced_job(namespace, label_selector=f"{LABEL_OPERATION_ID}={operation_id}").items
    if not jobs:
        return None
    job = jobs[0]
    labels = job.metadata.labels or {}
    status = job_status(job)
    result = _worker_result(core_api, namespace, operation_id) if status in ("succeeded", "failed") else None
    return {
        "operation_id": operation_id,
        "operation": labels.get(LABEL_OPERATION),
        "context": labels.get(LABEL_CONTEXT),
        "tenant": labels.get(LABEL_TENANT),
        "status": status,
        "job_name": job.metadata.name,
        "created_at": job.metadata.creation_timestamp,
        "result": result,
    }
