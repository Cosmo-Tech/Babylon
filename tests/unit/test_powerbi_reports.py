"""Tests for Power BI folder-based report discovery and tag generation."""

from pathlib import Path

import pytest

from Babylon.commands.macro.helpers.workspace.powerbi_helper import (
    _discover_powerbi_reports,
    _resolve_powerbi_reports,
)
from Babylon.utils.string import slugify_tag


# ---------------------------------------------------------------------------
# slugify_tag
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        ("Comparaison de scénarios", "comparaison_de_scenarios"),
        ("Scenario View", "scenario_view"),
        ("Revenue Analysis", "revenue_analysis"),
        ("Customer Overview", "customer_overview"),
        ("  Leading and trailing  ", "leading_and_trailing"),
        ("Weird!!Chars??.Here", "weird_chars_here"),
        ("", ""),
    ],
)
def test_slugify_tag(value, expected):
    assert slugify_tag(value) == expected


# ---------------------------------------------------------------------------
# _discover_powerbi_reports
# ---------------------------------------------------------------------------


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_discover_multiple_pbix_files(tmp_path):
    reports_dir = tmp_path / "dashboard" / "powerbi"
    _touch(reports_dir / "Comparaison de scénarios.pbix")
    _touch(reports_dir / "Scenario View.pbix")
    _touch(reports_dir / "Revenue Analysis.pbix")
    _touch(reports_dir / "Customer Overview.pbix")

    reports_config = {
        "path": "dashboard/powerbi",
        "parameters": [
            {"id": "Server", "value": "csm-cluster.postgres.database.azure.com"},
            {"id": "Database", "value": "tenant-mytenant"},
        ],
    }

    discovered = _discover_powerbi_reports(reports_config, tmp_path)

    assert len(discovered) == 4
    names = {r["name"] for r in discovered}
    assert names == {
        "Comparaison de scénarios",
        "Scenario View",
        "Revenue Analysis",
        "Customer Overview",
    }


def test_discover_generates_name_and_tag(tmp_path):
    reports_dir = tmp_path / "dashboard" / "powerbi"
    _touch(reports_dir / "Comparaison de scénarios.pbix")

    discovered = _discover_powerbi_reports({"path": "dashboard/powerbi"}, tmp_path)

    assert len(discovered) == 1
    report = discovered[0]
    assert report["name"] == "Comparaison de scénarios"
    assert report["tag"] == "comparaison_de_scenarios"
    assert report["path"].endswith("Comparaison de scénarios.pbix")


def test_discover_applies_shared_parameters_to_all_reports(tmp_path):
    reports_dir = tmp_path / "dashboard" / "powerbi"
    _touch(reports_dir / "Scenario View.pbix")
    _touch(reports_dir / "Revenue Analysis.pbix")

    shared_parameters = [
        {"id": "Server", "value": "csm-cluster.postgres.database.azure.com"},
        {"id": "Database", "value": "tenant-mytenant"},
    ]

    discovered = _discover_powerbi_reports(
        {"path": "dashboard/powerbi", "parameters": shared_parameters}, tmp_path
    )

    assert len(discovered) == 2
    for report in discovered:
        assert report["parameters"] == shared_parameters
        # Each report gets its own list instance (no shared mutable state).
        assert report["parameters"] is not shared_parameters


def test_discover_empty_folder_returns_no_reports(tmp_path):
    reports_dir = tmp_path / "dashboard" / "powerbi"
    reports_dir.mkdir(parents=True)

    discovered = _discover_powerbi_reports({"path": "dashboard/powerbi"}, tmp_path)

    assert discovered == []


def test_discover_ignores_non_pbix_files(tmp_path):
    reports_dir = tmp_path / "dashboard" / "powerbi"
    _touch(reports_dir / "Scenario View.pbix")
    _touch(reports_dir / "readme.txt")
    _touch(reports_dir / "notes.md")
    _touch(reports_dir / "archive.zip")

    discovered = _discover_powerbi_reports({"path": "dashboard/powerbi"}, tmp_path)

    assert len(discovered) == 1
    assert discovered[0]["name"] == "Scenario View"


def test_discover_handles_special_characters_in_names(tmp_path):
    reports_dir = tmp_path / "dashboard" / "powerbi"
    _touch(reports_dir / "Résumé (v2) - Q1_2026!.pbix")

    discovered = _discover_powerbi_reports({"path": "dashboard/powerbi"}, tmp_path)

    assert len(discovered) == 1
    report = discovered[0]
    assert report["name"] == "Résumé (v2) - Q1_2026!"
    assert report["tag"] == "resume_v2_q1_2026"


def test_discover_missing_path_key_returns_empty(tmp_path):
    assert _discover_powerbi_reports({}, tmp_path) == []


def test_discover_nonexistent_folder_returns_empty(tmp_path):
    assert _discover_powerbi_reports({"path": "does/not/exist"}, tmp_path) == []


# ---------------------------------------------------------------------------
# _resolve_powerbi_reports (dispatch between legacy list and folder discovery)
# ---------------------------------------------------------------------------


def test_resolve_reports_legacy_list_is_unchanged(tmp_path):
    legacy_reports = [
        {
            "name": "Comparaison de scénarios",
            "type": "dashboard",
            "path": "dashboard/powerbi/Comparaison de scénarios.pbix",
            "tag": "scenario_comparison",
            "parameters": [{"id": "Server", "value": "csm-cluster.postgres.database.azure.com"}],
        },
    ]

    resolved = _resolve_powerbi_reports(legacy_reports, tmp_path)

    assert resolved == legacy_reports


def test_resolve_reports_folder_based_dict(tmp_path):
    reports_dir = tmp_path / "dashboard" / "powerbi"
    _touch(reports_dir / "Scenario View.pbix")

    resolved = _resolve_powerbi_reports({"path": "dashboard/powerbi"}, tmp_path)

    assert len(resolved) == 1
    assert resolved[0]["name"] == "Scenario View"
    assert resolved[0]["tag"] == "scenario_view"


def test_resolve_reports_folder_based_yaml_list_item(tmp_path):
    """Reproduces the actual YAML shape produced by:

        reports:
          - path: "dashboard/powerbi"
            parameters:
              - id: "Server"
                value: "..."

    which parses as ``reports: [{"path": ..., "parameters": [...]}]`` a list
    containing a single discovery-spec dict (no ``name``/no explicit report
    list) rather than a bare mapping.
    """
    reports_dir = tmp_path / "dashboard" / "powerbi"
    _touch(reports_dir / "Comparaison de scénarios.pbix")
    _touch(reports_dir / "Scenario View.pbix")

    shared_parameters = [{"id": "Server", "value": "csm-cluster.postgres.database.azure.com"}]
    reports_yaml_list = [{"path": "dashboard/powerbi", "parameters": shared_parameters}]

    resolved = _resolve_powerbi_reports(reports_yaml_list, tmp_path)

    assert len(resolved) == 2
    names = {r["name"] for r in resolved}
    assert names == {"Comparaison de scénarios", "Scenario View"}
    for report in resolved:
        assert report["parameters"] == shared_parameters


def test_resolve_reports_mixed_legacy_and_discovery_entries(tmp_path):
    reports_dir = tmp_path / "dashboard" / "powerbi"
    _touch(reports_dir / "Scenario View.pbix")

    legacy_entry = {
        "name": "Manual Report",
        "path": "dashboard/other/Manual Report.pbix",
        "tag": "manual_report",
    }
    reports_config = [legacy_entry, {"path": "dashboard/powerbi"}]

    resolved = _resolve_powerbi_reports(reports_config, tmp_path)

    assert legacy_entry in resolved
    assert any(r["name"] == "Scenario View" for r in resolved)
    assert len(resolved) == 2


def test_resolve_reports_unsupported_type_returns_empty(tmp_path):
    assert _resolve_powerbi_reports("not-a-list-or-dict", tmp_path) == []
    assert _resolve_powerbi_reports(None, tmp_path) == []
