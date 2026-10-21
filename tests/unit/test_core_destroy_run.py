"""Tests of Babylon.core.operations.destroy and of the `babylon destroy` CLI wired to it.
"""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from Babylon.core import operations
from Babylon.core.errors import InvalidOptionsError
from Babylon.core.models import DestroyOptions, ResourceStatus
from Babylon.core.operations import destroy
from Babylon.utils.environment import Environment

# where each fake deleter clears its id (like the real helpers do on success)
ID_KEYS = {
    "solution": [("api", "solution_id")],
    "workspace": [("api", "workspace_id"), ("postgres", "schema_name")],
    "organization": [("api", "organization_id")],
    "webapp": [("webapp", "webapp_name")],
}


def full_state() -> dict:
    return {
        "context": "ctx",
        "tenant": "tenant-a",
        "remote": False,
        "services": {
            "api": {"organization_id": "o-1", "solution_id": "sol-1", "workspace_id": "w-1"},
            "webapp": {"webapp_name": "webapp-x", "webapp_url": ""},
            "postgres": {"schema_name": "s_1", "provider": ""},
        },
    }


@pytest.fixture
def setup(tmp_path: Path, monkeypatch) -> dict:
    """Isolated Babylon config dir with a local state file for ctx/tenant-a."""
    env = Environment()
    monkeypatch.setattr(env, "state_dir", tmp_path / "state")
    env.state_dir.mkdir()
    state_file = env.state_dir / "state.ctx.tenant-a.yaml"
    state_file.write_text(yaml.dump(full_state()))
    variables = tmp_path / "variables.yaml"
    variables.write_text("a: 1\n")
    return {"root": tmp_path, "state_file": state_file, "vars": variables}


def options(setup, **overrides) -> DestroyOptions:
    values = dict(context="ctx", tenant="tenant-a", variable_files=(setup["vars"],))
    values.update(overrides)
    return DestroyOptions(**values)


def fake_deleters(calls: list, broken: dict | None = None) -> dict:
    """Record calls and clear ids. `broken[resource]` = "silent" (helper logs, id stays) or an exception."""
    broken = broken or {}

    def make(resource):
        def deleter(state):
            calls.append(resource)
            behaviour = broken.get(resource)
            if isinstance(behaviour, BaseException):
                raise behaviour
            if behaviour == "silent":
                return  # like delete_api_resource on a 500: logs and returns, id kept
            for section, key in ID_KEYS[resource]:
                state["services"][section][key] = ""

        return deleter

    return {r: make(r) for r in ID_KEYS}


def read_state(setup) -> dict:
    return yaml.safe_load(setup["state_file"].read_text())


# core


def test_full_destroy_in_order_and_removes_state_file(setup):
    calls = []
    result = destroy(options(setup), deleters=fake_deleters(calls))
    assert calls == ["solution", "workspace", "organization", "webapp"]
    assert all(r.status == ResourceStatus.SUCCEEDED for r in result.resources)
    assert result.succeeded
    assert not setup["state_file"].exists()


def test_partial_destroy_keeps_other_ids_in_state(setup):
    calls = []
    result = destroy(options(setup, include=("workspace",)), deleters=fake_deleters(calls))
    assert calls == ["workspace"]
    assert result.succeeded
    api = read_state(setup)["services"]["api"]
    assert api == {"organization_id": "o-1", "solution_id": "sol-1", "workspace_id": ""}


def test_confirm_refused_touches_nothing(setup):
    calls, seen = [], []

    def refuse(plan):
        seen.extend(t.resource for t in plan)
        return False

    result = destroy(options(setup), confirm=refuse, deleters=fake_deleters(calls))
    assert result.cancelled and not result.succeeded
    assert seen == ["solution", "workspace", "organization", "webapp"]
    assert calls == []
    assert read_state(setup) == full_state()


def test_orphan_check_runs_before_confirm(setup):
    asked = []
    with pytest.raises(InvalidOptionsError, match="while keeping workspace"):
        destroy(options(setup, exclude=("workspace",)), confirm=lambda p: asked.append(p) or True, deleters=fake_deleters([]))
    assert asked == []  # the user is not even asked


def test_not_deployed_resource_is_skipped(setup):
    state = full_state()
    state["services"]["webapp"]["webapp_name"] = ""
    setup["state_file"].write_text(yaml.dump(state))
    calls = []
    result = destroy(options(setup), deleters=fake_deleters(calls))
    assert "webapp" not in calls
    assert (result.resources[-1].status, result.resources[-1].error) == (ResourceStatus.SKIPPED, "not deployed")
    assert result.succeeded


@pytest.mark.parametrize(
    "behaviour, expected_error",
    [
        ("silent", "still present in state"),  # helper swallowed the error
        (SystemExit(1), "exit code 1"),
        (RuntimeError("api down"), "RuntimeError: api down"),
    ],
)
def test_failure_stops_and_state_keeps_what_was_not_deleted(setup, behaviour, expected_error):
    calls = []
    result = destroy(options(setup), deleters=fake_deleters(calls, {"workspace": behaviour}))
    assert calls == ["solution", "workspace"]  # fail_fast: organization never deleted
    assert [r.status for r in result.resources] == [
        ResourceStatus.SUCCEEDED,
        ResourceStatus.FAILED,
        ResourceStatus.SKIPPED,
        ResourceStatus.SKIPPED,
    ]
    assert expected_error in result.resources[1].error
    # The state is saved anyway: solution is gone, the rest is still recorded.
    api = read_state(setup)["services"]["api"]
    assert api == {"organization_id": "o-1", "solution_id": "", "workspace_id": "w-1"}


# CLI


@pytest.fixture
def cli(setup, monkeypatch):
    from Babylon.main import main

    env = Environment()
    (env.state_dir / "namespace.yaml").write_text("context: ctx\ntenant: tenant-a\n")
    monkeypatch.chdir(setup["root"])

    def run(*args, input=None):
        return CliRunner().invoke(main, ["--log-path", str(setup["root"]), "destroy", *args], input=input)

    return run


def test_cli_destroy_yes(cli, setup, monkeypatch):
    calls = []
    monkeypatch.setattr(operations, "default_deleters", lambda: fake_deleters(calls))
    res = cli("-y")
    assert res.exit_code == 0, res.output
    assert calls == ["solution", "workspace", "organization", "webapp"]
    assert "Cleanup process complete" in res.output
    assert not setup["state_file"].exists()


def test_cli_destroy_answer_no(cli, setup, monkeypatch):
    calls = []
    monkeypatch.setattr(operations, "default_deleters", lambda: fake_deleters(calls))
    res = cli(input="n\n")
    assert res.exit_code == 0, res.output
    assert "Deletion cancelled" in res.output
    assert calls == []
    assert setup["state_file"].exists()


def test_cli_destroy_failure_exits_1(cli, monkeypatch):
    monkeypatch.setattr(operations, "default_deleters", lambda: fake_deleters([], {"solution": "silent"}))
    res = cli("-y")
    assert res.exit_code == 1
    assert "1 resource(s) failed to destroy" in res.output
    assert "Cleanup process complete" not in res.output


def test_cli_destroy_orphan_is_a_clean_error(cli):
    res = cli("-y", "--exclude", "workspace")
    assert res.exit_code == 1
    assert "Error: Cannot destroy" in res.output
