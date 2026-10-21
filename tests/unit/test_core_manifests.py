from pathlib import Path

import pytest

from Babylon.core.errors import InvalidOptionsError
from Babylon.core.manifests import load_manifest, load_manifests, plan_apply
from Babylon.core.models import ApplyResult, ResourceOutcome, ResourceStatus
from Babylon.core.selection import resolve_resources


def write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text)
    return path


def manifest_text(kind: str) -> str:
    return f"kind: {kind}\nnamespace:\n  remote: false\nspec:\n  payload:\n    name: {{{{ org_name }}}}\n"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    write(tmp_path, "Workspace.yaml", manifest_text("Workspace"))
    write(tmp_path, "Solution.yaml", manifest_text("Solution"))
    write(tmp_path, "b_Organization.yaml", manifest_text("Organization"))
    write(tmp_path, "a_Organization.yml", manifest_text("Organization"))
    write(tmp_path, "Webapp.yaml", manifest_text("Webapp"))
    write(tmp_path, "notes.txt", "not a manifest")
    write(tmp_path, "other.yaml", "kind: SomethingElse\n")
    (tmp_path / "postgres").mkdir()
    write(tmp_path / "postgres", "Organization.yaml", manifest_text("Organization"))  # sub-folder: ignored
    return tmp_path


def test_load_manifest_reads_kind_namespace_and_converts_template_syntax(tmp_path):
    m = load_manifest(write(tmp_path, "Organization.yaml", manifest_text("Organization")))
    assert m.resource == "organization"
    assert m.namespace == "remote: false\n"
    assert "${ org_name }" in m.content
    assert "{{" not in m.content


def test_load_manifest_ignores_unknown_kind(tmp_path):
    assert load_manifest(write(tmp_path, "x.yaml", "kind: Foo\n")) is None


@pytest.mark.parametrize("text", ["kind: [unclosed", "", "- just\n- a list\n"])
def test_load_manifest_rejects_invalid_files(tmp_path, text):
    with pytest.raises(InvalidOptionsError):
        load_manifest(write(tmp_path, "bad.yaml", text))


def test_load_manifests_keeps_top_level_yaml_files_sorted(project):
    names = [m.path.name for m in load_manifests(project)]
    assert names == ["Solution.yaml", "Webapp.yaml", "Workspace.yaml", "a_Organization.yml", "b_Organization.yaml"]


def test_load_manifests_missing_directory(tmp_path):
    with pytest.raises(InvalidOptionsError, match="not found"):
        load_manifests(tmp_path / "missing")


def test_plan_apply_follows_dependency_order(project):
    plan = plan_apply(load_manifests(project), resolve_resources())
    assert [(m.resource, m.path.name) for m in plan] == [
        ("organization", "a_Organization.yml"),
        ("organization", "b_Organization.yaml"),
        ("solution", "Solution.yaml"),
        ("webapp", "Webapp.yaml"),
        ("workspace", "Workspace.yaml"),
    ]


def test_plan_apply_respects_selection(project):
    plan = plan_apply(load_manifests(project), resolve_resources(exclude=["organization", "webapp"]))
    assert [m.resource for m in plan] == ["solution", "workspace"]


def test_apply_result_succeeded_only_when_everything_succeeded():
    ok = ResourceOutcome("organization", "Organization.yaml", ResourceStatus.SUCCEEDED)
    ko = ResourceOutcome("solution", "Solution.yaml", ResourceStatus.FAILED, "boom")
    assert ApplyResult("ctx", "tenant", [ok]).succeeded
    assert not ApplyResult("ctx", "tenant", [ok, ko]).succeeded
