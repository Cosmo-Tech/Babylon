"""Tests of the Babylon API, health check and request validation (nothing is executed)."""

import pytest
from fastapi.testclient import TestClient

from babylon_api.app import app

client = TestClient(app)


def apply_body(**overrides) -> dict:
    body = {
        "repository": {"url": "https://github.com/acme/deployments", "ref": "main"},
        "deploy_dir": "projects/brewery",
        "context": "dev",
        "tenant": "tenant-a",
    }
    body.update(overrides)
    return body


def errors_of(res) -> str:
    """All 422 messages as one string (pydantic returns a list of errors)."""
    detail = res.json()["detail"]
    return str(detail if isinstance(detail, str) else [e["msg"] for e in detail])


def test_healthz():
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_valid_apply_is_echoed_with_defaults():
    res = client.post("/apply", json=apply_body())
    assert res.status_code == 200, res.text
    body = res.json()
    assert (body["status"], body["operation"]) == ("validated", "apply")
    assert body["request"]["variable_files"] == ["variables.yaml"]  # default
    assert body["request"]["include"] == [] and body["request"]["exclude"] == []


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"tenant": "Tenant_A"}, "lowercase letters"),  # not a valid Kubernetes namespace
        ({"context": "-dev"}, "lowercase letters"),
        ({"deploy_dir": "../../etc"}, "inside the repository"),  # path traversal
        ({"deploy_dir": "/etc"}, "inside the repository"),
        ({"variable_files": ["ok.yaml", "../secret.yaml"]}, "inside the repository"),
        ({"repository": {"url": "http://github.com/acme/x"}}, "https"),
        ({"repository": {"url": "https://github.com/acme/x", "ref": "--upload-pack=evil"}}, "invalid git ref"),
        ({"include": ["solutoin"]}, "Invalid resource type(s): solutoin"),  # message from the core
        ({"include": ["solution"], "exclude": ["webapp"]}, "include"),  # include XOR exclude
        ({"exlude": ["webapp"]}, "Extra inputs are not permitted"),  # typo is not silently ignored
    ],
)
def test_invalid_apply_is_rejected_with_422(overrides, expected):
    res = client.post("/apply", json=apply_body(**overrides))
    assert res.status_code == 422
    assert expected in errors_of(res)


def test_apply_requires_deploy_dir():
    body = apply_body()
    del body["deploy_dir"]
    assert client.post("/apply", json=body).status_code == 422


def destroy_body(**overrides) -> dict:
    body = apply_body(confirm=True, **overrides)
    del body["deploy_dir"]
    return body


def test_valid_destroy():
    res = client.post("/destroy", json=destroy_body())
    assert res.status_code == 200, res.text
    assert res.json()["operation"] == "destroy"


@pytest.mark.parametrize("confirm", [False, "yes", None])
def test_destroy_requires_explicit_confirm_true(confirm):
    body = destroy_body()
    body["confirm"] = confirm
    assert client.post("/destroy", json=body).status_code == 422
    del body["confirm"]
    assert client.post("/destroy", json=body).status_code == 422


def test_openapi_schema_is_generated():
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/healthz", "/apply", "/destroy"} <= set(paths)
