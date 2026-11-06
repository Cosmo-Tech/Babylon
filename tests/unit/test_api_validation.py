"""Tests of the Babylon API: health check and request validation."""

import pytest


def apply_body(**overrides) -> dict:
    body = {
        "repository": {"url": "https://github.com/acme/deployments", "ref": "main"},
        "deploy_dir": "projects/brewery",
        "context": "dev",
    }
    body.update(overrides)
    return body


def destroy_body(**overrides) -> dict:
    return {"context": "dev", "confirm": True, **overrides}


def errors_of(res) -> str:
    """All 422 messages as one string (pydantic returns a list of errors)."""
    detail = res.json()["detail"]
    return str(detail if isinstance(detail, str) else [e["msg"] for e in detail])


def test_healthz(api):
    res = api.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_valid_apply_is_accepted(api, fake_kube):
    res = api.post("/apply", json=apply_body())
    assert res.status_code == 202, res.text
    assert res.json()["operation"] == "apply"
    assert len(fake_kube.batch.jobs) == 1


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"context": "Dev_1"}, "lowercase letters"),  # not a valid Kubernetes name
        ({"context": "-dev"}, "lowercase letters"),
        ({"deploy_dir": "../../etc"}, "inside the repository"),  # path traversal
        ({"deploy_dir": "/etc"}, "inside the repository"),
        ({"variable_files": ["ok.yaml", "../secret.yaml"]}, "inside the repository"),
        ({"repository": {"url": "http://github.com/acme/x"}}, "https"),
        ({"repository": {"url": "https://github.com/acme/x", "ref": "--upload-pack=evil"}}, "invalid git ref"),
        ({"include": ["solutoin"]}, "Invalid resource type(s): solutoin"),  # message from the core
        ({"include": ["solution"], "exclude": ["workspace"]}, "include"),  # include XOR exclude
        ({"exlude": ["solution"]}, "Extra inputs are not permitted"),  # typo is not silently ignored
        ({"include": ["webapp"]}, "Not supported by Babylon API: webapp"),
        ({"exclude": ["webapp"]}, "Not supported by Babylon API: webapp"),
    ],
)
def test_invalid_apply_is_rejected_with_422_and_no_job(api, fake_kube, overrides, expected):
    res = api.post("/apply", json=apply_body(**overrides))
    assert res.status_code == 422
    assert expected in errors_of(res)
    assert fake_kube.batch.jobs == []


def test_apply_requires_deploy_dir(api):
    body = apply_body()
    del body["deploy_dir"]
    assert api.post("/apply", json=body).status_code == 422


def test_valid_destroy(api):
    res = api.post("/destroy", json=destroy_body())
    assert res.status_code == 202, res.text
    assert res.json()["operation"] == "destroy"


@pytest.mark.parametrize("route, body", [("/apply", apply_body), ("/destroy", destroy_body)])
@pytest.mark.parametrize("tenant", ["tenant-a", "other-tenant", ""])
def test_client_cannot_provide_the_tenant(api, fake_kube, route, body, tenant):
    """Even the right value is refused: the tenant is the API namespace, not a client choice."""
    res = api.post(route, json=body(tenant=tenant))
    assert res.status_code == 422
    assert "The tenant is automatically injected by the backend and must not be provided by the client." in errors_of(res)
    assert fake_kube.batch.jobs == []


@pytest.mark.parametrize("field", [{"repository": {"url": "https://github.com/acme/x"}}, {"variable_files": ["v.yaml"]}])
def test_destroy_takes_no_repository(api, fake_kube, field):
    """Destroy works from the state Secret only: sending repository/variables is an error, not ignored."""
    res = api.post("/destroy", json=destroy_body(**field))
    assert res.status_code == 422
    assert "Extra inputs are not permitted" in errors_of(res)
    assert fake_kube.batch.jobs == []


@pytest.mark.parametrize("confirm", [False, "yes", None])
def test_destroy_requires_explicit_confirm_true(api, fake_kube, confirm):
    body = destroy_body()
    body["confirm"] = confirm
    assert api.post("/destroy", json=body).status_code == 422
    del body["confirm"]
    assert api.post("/destroy", json=body).status_code == 422
    assert fake_kube.batch.jobs == []


def test_openapi_schema_is_generated(api):
    paths = api.get("/openapi.json").json()["paths"]
    assert {"/healthz", "/apply", "/destroy", "/operations/{operation_id}"} <= set(paths)
