"""Tests of Babylon.core.operations.apply and of the `babylon apply` CLI wired to it."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from Babylon.core import operations
from Babylon.core.errors import InvalidOptionsError, OperationInProgressError, UnknownResourceError
from Babylon.core.models import ApplyOptions, ResourceStatus
from Babylon.core.operations import apply
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

RESOURCES = ("build", "organization", "solution", "webapp", "workspace")


def manifest_text(kind: str) -> str:
    return f"kind: {kind}\nnamespace:\n  remote: false\nspec:\n  payload: {{}}\n"


@pytest.fixture
def project(tmp_path: Path) -> dict:
    deploy = tmp_path / "project"
    deploy.mkdir()
    for kind in ("Organization", "Solution", "Workspace"):
        (deploy / f"{kind}.yaml").write_text(manifest_text(kind))
    variables = tmp_path / "variables.yaml"
    variables.write_text("a: 1\n")
    return {"dir": deploy, "vars": variables, "root": tmp_path}


def options(project, **overrides) -> ApplyOptions:
    values = dict(deploy_dir=project["dir"], context="ctx", tenant="tenant-a", variable_files=(project["vars"],))
    values.update(overrides)
    return ApplyOptions(**values)


def fake_deployers(calls: list, behaviours: dict | None = None) -> dict:
    """Record every call; `behaviours[resource]` is called to produce the return value / raise."""
    behaviours = behaviours or {}

    def make(resource):
        def deployer(manifest, deploy_dir):
            calls.append(resource)
            if resource in behaviours:
                return behaviours[resource]()
            return None

        return deployer

    return {r: make(r) for r in RESOURCES}


def boom_exit():
    raise SystemExit(1)


def boom_error():
    raise RuntimeError("api down")


# API core


def test_apply_deploys_in_order_and_reports_success(project):
    calls = []
    result = apply(options(project), deployers=fake_deployers(calls))
    assert calls == ["organization", "solution", "workspace"]
    assert [(r.resource, r.status) for r in result.resources] == [
        ("organization", ResourceStatus.SUCCEEDED),
        ("solution", ResourceStatus.SUCCEEDED),
        ("workspace", ResourceStatus.SUCCEEDED),
    ]
    assert result.succeeded


def test_apply_respects_include(project):
    calls = []
    apply(options(project, include=("solution",)), deployers=fake_deployers(calls))
    assert calls == ["solution"]


@pytest.mark.parametrize(
    "behaviour, expected_error",
    [
        (CommandResponse.fail, "deployment reported a failure"),  # what deploy_* return on error
        (boom_exit, "exit code 1"),  # sys.exit() in a helper
        (boom_error, "RuntimeError: api down"),  # SDK / HTTP exception
    ],
)
def test_failure_stops_and_next_resources_are_skipped(project, behaviour, expected_error):
    calls = []
    result = apply(options(project), deployers=fake_deployers(calls, {"solution": behaviour}))
    assert calls == ["organization", "solution"]  # fail_fast: workspace never deployed
    assert [r.status for r in result.resources] == [
        ResourceStatus.SUCCEEDED,
        ResourceStatus.FAILED,
        ResourceStatus.SKIPPED,
    ]
    assert expected_error in result.resources[1].error
    assert result.resources[2].error == "previous resource failed"
    assert not result.succeeded


def test_without_fail_fast_next_resources_still_run(project):
    calls = []
    result = apply(options(project, fail_fast=False), deployers=fake_deployers(calls, {"solution": CommandResponse.fail}))
    assert calls == ["organization", "solution", "workspace"]
    assert result.resources[2].status == ResourceStatus.SUCCEEDED


def test_remote_does_not_leak_from_a_previous_operation(project):
    env = Environment()
    env.remote = True  # e.g. left over by a previous apply on another tenant
    seen = []
    deployers = fake_deployers([])
    deployers["organization"] = lambda m, d: seen.append(env.remote)
    apply(options(project, include=("organization",)), deployers=deployers)
    assert seen == [False]
    assert env.remote is True  # restored afterwards


def test_invalid_options_fail_before_any_deployment(project):
    calls = []
    with pytest.raises(UnknownResourceError):
        apply(options(project, include=("solutoin",)), deployers=fake_deployers(calls))
    (project["dir"] / "broken.yaml").write_text("")
    with pytest.raises(InvalidOptionsError):
        apply(options(project), deployers=fake_deployers(calls))
    assert calls == []


def test_environment_is_bound_during_operation_and_restored_after(project):
    env = Environment()
    env.set_context("before")
    env.set_environ("before-tenant")
    seen = {}

    def spy(manifest, deploy_dir):
        seen.update(context=env.context_id, tenant=env.environ_id, files=list(env.variable_files))

    deployers = fake_deployers([])
    deployers["organization"] = spy
    apply(options(project, include=("organization",)), deployers=deployers)

    assert seen == {"context": "ctx", "tenant": "tenant-a", "files": [project["vars"]]}
    assert (env.context_id, env.environ_id) == ("before", "before-tenant")


def test_second_operation_in_same_process_is_refused(project):
    errors = []

    def reentrant(manifest, deploy_dir):
        try:
            apply(options(project), deployers=fake_deployers([]))
        except OperationInProgressError as exc:
            errors.append(exc)

    deployers = fake_deployers([])
    deployers["organization"] = reentrant
    apply(options(project, include=("organization",)), deployers=deployers)
    assert len(errors) == 1
    # The lock is released at the end: a new operation works.
    assert apply(options(project), deployers=fake_deployers([])).succeeded


def test_command_response_works_outside_click():
    assert CommandResponse.fail().has_failed()


# CLI


@pytest.fixture
def cli(project, monkeypatch):
    """Run `babylon apply` in the project folder with an isolated Babylon config dir."""
    from Babylon.main import main

    env = Environment()
    monkeypatch.setattr(env, "state_dir", project["root"] / "state")
    env.state_dir.mkdir()
    (env.state_dir / "namespace.yaml").write_text("context: ctx\ntenant: tenant-a\n")
    monkeypatch.chdir(project["root"])

    def run(*args):
        return CliRunner().invoke(main, ["--log-path", str(project["root"]), "apply", "project", *args])

    return run


def test_cli_apply_uses_core(cli, monkeypatch):
    calls = []
    monkeypatch.setattr(operations, "default_deployers", lambda: fake_deployers(calls))
    res = cli("--exclude", "workspace")
    assert res.exit_code == 0, res.output
    assert calls == ["organization", "solution"]
    assert "Deployment process complete" in res.output


def test_cli_apply_exits_1_when_a_resource_fails(cli, monkeypatch):
    calls = []
    monkeypatch.setattr(operations, "default_deployers", lambda: fake_deployers(calls, {"solution": CommandResponse.fail}))
    res = cli()
    assert calls == ["organization", "solution"]
    assert res.exit_code == 1
    assert "1 resource(s) failed to deploy" in res.output
    assert "Deployment process complete" not in res.output


def test_cli_apply_invalid_yaml_is_a_clean_click_error(cli, project):
    (project["dir"] / "broken.yaml").write_text("")
    res = cli()
    assert res.exit_code == 1
    assert "Error: broken.yaml" in res.output
    assert "InvalidOptionsError" not in res.output


def test_cli_apply_keeps_include_exclude_messages(cli):
    res = cli("--include", "solution", "--exclude", "build")
    assert res.exit_code == 1
    assert "Argument Conflict" in res.output
