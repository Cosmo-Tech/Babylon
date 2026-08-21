"""Tests for the dataviz provider dispatch used by the Destroy Macro Command."""

from Babylon.commands.macro.helpers.workspace import superset_helper as sh


def test_destroy_dashboard_assets_dispatches_to_powerbi(monkeypatch):
    called = {}

    def _fake_destroy_powerbi_assets(state):
        called["state"] = state
        return True

    monkeypatch.setattr(sh, "destroy_powerbi_assets", _fake_destroy_powerbi_assets)

    state = {"services": {"api": {"workspace_id": "ws1"}}}
    assert sh.destroy_dashboard_assets("powerbi", state, {}) is True
    assert called["state"] is state


def test_destroy_dashboard_assets_dispatches_to_superset(monkeypatch):
    called = {}

    def _fake_delete_superset_assets(base_url, superset_config, workspace_id):
        called["base_url"] = base_url
        called["workspace_id"] = workspace_id
        return True

    monkeypatch.setattr(sh, "delete_superset_assets", _fake_delete_superset_assets)

    state = {"services": {"api": {"workspace_id": "ws1"}}}
    config = {"superset_url": "https://superset.example.com/"}

    assert sh.destroy_dashboard_assets("superset", state, config) is True
    assert called == {"base_url": "https://superset.example.com", "workspace_id": "ws1"}


def test_destroy_dashboard_assets_superset_without_url_is_noop_success():
    state = {"services": {"api": {"workspace_id": "ws1"}}}
    assert sh.destroy_dashboard_assets("superset", state, {}) is True


def test_destroy_dashboard_assets_unsupported_provider_is_noop_success():
    state = {"services": {"api": {"workspace_id": "ws1"}}}
    assert sh.destroy_dashboard_assets("unknown", state, {}) is True
