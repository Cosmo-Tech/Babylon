"""Tests of babylon_api.worker: the code that runs inside the Job."""

import json
from pathlib import Path

import pytest

from Babylon.core.errors import BabylonError, InvalidOptionsError
from Babylon.utils.environment import Environment
from babylon_api import worker
from babylon_api.repository import Checkout

APPLY = {
    "repository": {"url": "https://github.com/acme/deployments", "ref": "main"},
    "deploy_dir": "project",
    "context": "dev",
    "tenant": "tenant-a",
}
DESTROY = {"context": "dev", "tenant": "tenant-a", "confirm": True}


@pytest.fixture
def checkout(tmp_path, monkeypatch) -> dict:
    """Replace the git fetch by a prepared directory; record what was asked."""
    repo = tmp_path / "repo"
    (repo / "project").mkdir(parents=True)
    (repo / "project" / "Organization.yaml").write_text("kind: Organization\nnamespace:\n  remote: false\nspec: {}\n")
    (repo / "variables.yaml").write_text("a: 1\n")
    asked = {}

    def fake_prepare(url, ref, dest, deploy_dir, variable_files, environ=None):
        asked.update(url=url, ref=ref, deploy_dir=deploy_dir)
        return Checkout(
            root=repo,
            commit="c0ffee",
            deploy_dir=repo / deploy_dir if deploy_dir else None,
            variable_files=tuple(repo / f for f in variable_files),
        )

    monkeypatch.setattr(worker, "prepare_checkout", fake_prepare)
    monkeypatch.setattr(Environment(), "state_dir", Environment().state_dir)  # restored after the test
    return asked


def test_apply_runs_core_with_remote_state_forced(tmp_path, checkout):
    seen = {}

    def deployer(manifest, deploy_dir):
        env = Environment()
        seen.update(remote=env.remote, tenant=env.environ_id, files=[p.name for p in env.variable_files])

    summary = worker.run({"operation": "apply", "request": APPLY}, tmp_path / "work", deployers={"organization": deployer})
    assert summary["status"] == "succeeded"
    assert summary["commit"] == "c0ffee"
    assert summary["resources"] == [{"resource": "organization", "file": "Organization.yaml", "status": "succeeded", "error": None}]
    # The manifest says remote: false, but in a pod the state must live in the Kubernetes Secret.
    assert seen == {"remote": True, "tenant": "tenant-a", "files": ["variables.yaml"]}
    assert checkout == {"url": "https://github.com/acme/deployments", "ref": "main", "deploy_dir": "project"}


def test_manifest_cannot_turn_forced_remote_off(tmp_path, checkout):
    seen = []

    def deployer(manifest, deploy_dir):
        env = Environment()
        env.get_ns_from_text(manifest.content)  # what the real deployers do with the `namespace:` block
        seen.append(env.remote)

    worker.run({"operation": "apply", "request": APPLY}, tmp_path / "work", deployers={"organization": deployer})
    assert seen == [True]


def test_destroy_does_not_ask_and_fetches_nothing(tmp_path, checkout, monkeypatch):
    captured = {}

    def fake_destroy(options, confirm=None, deleters=None):
        captured.update(confirm=confirm, force_remote=options.force_remote, files=options.variable_files, include=options.include)
        from Babylon.core.models import DestroyResult

        return DestroyResult(context=options.context, tenant=options.tenant, nothing_to_destroy=True)

    monkeypatch.setattr(worker, "core_destroy", fake_destroy)
    summary = worker.run({"operation": "destroy", "request": DESTROY}, tmp_path / "work", deleters={})
    assert summary["status"] == "succeeded"
    # No repository, no variables, and webapp never selected.
    assert captured == {
        "confirm": None,
        "force_remote": True,
        "files": (),
        "include": ("build", "organization", "solution", "workspace"),
    }
    assert checkout == {}  # nothing fetched


def test_apply_never_selects_webapp(tmp_path, checkout):
    called = []
    deployers = {r: (lambda m, d, r=r: called.append(r)) for r in ("organization", "webapp")}
    repo_project = Path(tmp_path / "repo" / "project")
    (repo_project / "WebApp.yaml").write_text("kind: WebApp\nnamespace:\n  remote: false\nspec: {}\n")
    worker.run({"operation": "apply", "request": APPLY}, tmp_path / "work", deployers=deployers)
    assert called == ["organization"]


@pytest.mark.parametrize("provider", ["powerbi", "", None])
def test_workspace_destroy_refuses_external_postgres(provider):
    deleted = []
    guarded = worker.only_internal_postgres(deleted.append)
    with pytest.raises(BabylonError, match="not supported by Babylon API"):
        guarded({"services": {"postgres": {"provider": provider}}})
    assert deleted == []


def test_workspace_destroy_allows_internal_postgres():
    deleted = []
    state = {"services": {"postgres": {"provider": "Superset"}}}
    worker.only_internal_postgres(deleted.append)(state)
    assert deleted == [state]


@pytest.mark.parametrize(
    "payload, error",
    [
        ({"operation": "rm -rf", "request": APPLY}, "unknown operation"),
        ({"operation": "apply", "request": {**APPLY, "tenant": "Bad_Tenant"}}, "lowercase"),  # validated again
        ({"operation": "destroy", "request": {**DESTROY, "confirm": False}}, "confirm"),
    ],
)
def test_bad_payload_is_refused_before_fetching(tmp_path, checkout, payload, error):
    with pytest.raises(ValueError, match=error):
        worker.run(payload, tmp_path / "work")
    assert checkout == {}  # nothing fetched


def test_worker_refuses_a_tenant_other_than_its_namespace(tmp_path, checkout, monkeypatch):
    monkeypatch.setenv("BABYLON_LOCK_NAMESPACE", "tenant-b")
    with pytest.raises(ValueError, match="not the namespace of this Job"):
        worker.run({"operation": "apply", "request": APPLY}, tmp_path / "work")
    assert checkout == {}


# main: what the container really executes


@pytest.fixture
def result_file(tmp_path) -> Path:
    return tmp_path / "termination-log"


def run_main(result_file, **env):
    code = worker.main({worker.RESULT_PATH_ENV: str(result_file), **env})
    return code, json.loads(result_file.read_text())


def test_main_success_writes_result_and_exits_0(result_file, monkeypatch):
    monkeypatch.setattr(worker, "run", lambda payload, workdir, **_: {"status": "succeeded", "commit": "c0ffee"})
    code, result = run_main(result_file, BABYLON_OPERATION=json.dumps({"operation": "apply", "request": APPLY}))
    assert (code, result) == (0, {"status": "succeeded", "commit": "c0ffee"})


def test_main_failure_exits_1(result_file, monkeypatch):
    def failing(payload, workdir, **_):
        raise InvalidOptionsError("'project' is not a directory of the repository")

    monkeypatch.setattr(worker, "run", failing)
    code, result = run_main(result_file, BABYLON_OPERATION="{}")
    assert code == 1
    assert result == {"status": "failed", "error": "InvalidOptionsError: 'project' is not a directory of the repository"}


@pytest.mark.parametrize("env, error", [({}, "BABYLON_OPERATION is not set"), ({"BABYLON_OPERATION": "{not json"}, "JSONDecodeError")])
def test_main_bad_input(result_file, env, error):
    code, result = run_main(result_file, **env)
    assert code == 1 and error in result["error"]


def test_result_always_fits_in_a_termination_message():
    huge = {"status": "failed", "resources": [{"resource": "x", "error": "e" * 300}] * 100}
    text = worker.fit(huge)
    assert len(text.encode()) <= worker.MAX_RESULT_BYTES
    assert json.loads(text)["status"] == "failed"
