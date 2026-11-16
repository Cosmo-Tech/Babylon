"""One operation at a time per (context, tenant), with a Kubernetes Lease.

Why: two Jobs on the same tenant would both read, modify and write the same state Secret
(`babylon-state-<context>-<tenant>`): the last writer wins and resource ids are lost.

A Lease (coordination.k8s.io/v1) is a tiny Kubernetes object made for this. Kubernetes
guarantees that only one `create` of a given name succeeds, and that a `replace` with an
old resourceVersion is refused (409). These two guarantees make the lock safe even if two
workers start at the same millisecond.

The lock has an expiry (lease_duration_seconds) so that a worker killed without cleanup
(OOM, node lost, deadline) cannot block a tenant forever.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from kubernetes import client
from kubernetes.client.exceptions import ApiException

from Babylon.core.errors import OperationInProgressError

logger = logging.getLogger(__name__)

LABEL_MANAGED_BY = "app.kubernetes.io/managed-by"
MANAGED_BY = "babylon-api"


def lease_name(context: str, tenant: str) -> str:
    # context and tenant are validated Kubernetes names the result is a valid object name.
    return f"babylon-lock-{context}-{tenant}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(spec: client.V1LeaseSpec, now: datetime) -> bool:

    if not spec or not spec.holder_identity:
        return True  # released

    renewed = spec.renew_time or spec.acquire_time
    if renewed is None or not spec.lease_duration_seconds:
        return True

    return renewed + timedelta(seconds=spec.lease_duration_seconds) < now


def acquire(api: client.CoordinationV1Api, namespace: str, name: str, holder: str, duration: int) -> None:
    """Take the lock or raise OperationInProgressError. Never waits."""

    now = _now()
    spec = client.V1LeaseSpec(holder_identity=holder, lease_duration_seconds=duration, acquire_time=now, renew_time=now)

    try:
        api.create_namespaced_lease(
            namespace,
            client.V1Lease(metadata=client.V1ObjectMeta(name=name, labels={LABEL_MANAGED_BY: MANAGED_BY}), spec=spec),
        )
        return  # nobody had it
    except ApiException as exc:
        if exc.status != 409:
            raise

    # The Lease exists: free, expired, or held by someone else.
    existing = api.read_namespaced_lease(name, namespace)

    if existing.spec and existing.spec.holder_identity == holder:
        return  # already ours (e.g. retry of the same operation)

    if not _is_expired(existing.spec, now):
        raise OperationInProgressError(f"Operation {existing.spec.holder_identity} is already running on this context/tenant")

    if existing.spec and existing.spec.holder_identity:
        logger.warning(f"lock {name}: taking over the expired lock of operation {existing.spec.holder_identity}")

    existing.spec = spec

    try:
        # metadata.resource_version is kept: if someone changed the Lease since our read, Kubernetes answers 409.
        api.replace_namespaced_lease(name, namespace, existing)
    except ApiException as exc:
        if exc.status == 409:
            raise OperationInProgressError("Another operation took the lock at the same time") from None
        raise


def release(api: client.CoordinationV1Api, namespace: str, name: str, holder: str) -> None:
    """Delete the Lease, only if we still hold it. Errors are logged, never raised."""

    try:
        existing = api.read_namespaced_lease(name, namespace)

        if not existing.spec or existing.spec.holder_identity != holder:
            logger.warning(f"lock {name}: not released, it is held by {existing.spec and existing.spec.holder_identity}")
            return

        # Precondition: delete only the version we just read (not a Lease re-taken in between).
        api.delete_namespaced_lease(
            name,
            namespace,
            body=client.V1DeleteOptions(preconditions=client.V1Preconditions(resource_version=existing.metadata.resource_version)),
        )
    except ApiException as exc:
        if exc.status not in (404, 409):
            logger.warning(f"lock {name}: release failed ({exc.status} {exc.reason}), it will expire by itself")


@contextmanager
def tenant_lock(
    api: client.CoordinationV1Api, namespace: str, context: str, tenant: str, holder: str, duration: int
) -> Iterator[None]:
    """`with tenant_lock(...):` = acquire, run, always release (even after an exception)."""

    name = lease_name(context, tenant)

    acquire(api, namespace, name, holder, duration)
    try:
        yield
    finally:
        release(api, namespace, name, holder)
