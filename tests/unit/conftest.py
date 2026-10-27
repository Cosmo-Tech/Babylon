"""Shared fixtures for the API tests: a fake Kubernetes, no cluster needed."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from kubernetes import client

from babylon_api.app import KubeClients, app, get_kube, get_settings
from babylon_api.jobs import JobSettings

SETTINGS = JobSettings(namespace="babylon", image="babylon:test", service_account="babylon-worker", secret_name="babylon-worker")


def matches(labels: dict | None, selector: str) -> bool:
    """Kubernetes equality selector: "a=b,c=d" (all must match)."""
    labels = labels or {}
    return all(labels.get(k) == v for k, v in (part.split("=", 1) for part in selector.split(",")))


class FakeBatch:
    """Keeps created Jobs in memory, like the Kubernetes API would."""

    def __init__(self):
        self.jobs: list[client.V1Job] = []

    def create_namespaced_job(self, namespace, body):
        assert namespace == body.metadata.namespace
        self.jobs.append(body)
        return body

    def list_namespaced_job(self, namespace, label_selector):
        items = [j for j in self.jobs if j.metadata.namespace == namespace and matches(j.metadata.labels, label_selector)]
        return SimpleNamespace(items=items)


class FakeCore:
    def __init__(self):
        self.pods: list[client.V1Pod] = []

    def list_namespaced_pod(self, namespace, label_selector):
        return SimpleNamespace(items=[p for p in self.pods if matches(p.metadata.labels, label_selector)])


@pytest.fixture
def fake_kube():
    kube = KubeClients(batch=FakeBatch(), core=FakeCore())
    app.dependency_overrides[get_kube] = lambda: kube
    app.dependency_overrides[get_settings] = lambda: SETTINGS
    yield kube
    app.dependency_overrides.clear()


@pytest.fixture
def api(fake_kube) -> TestClient:
    return TestClient(app)
