"""Tests for the Power BI teardown helpers used by the Destroy Macro Command."""

from Babylon.commands.macro.helpers.workspace import powerbi_helper as pbh


class _FakeDatasetService:
    def __init__(self, datasets=None, fail_ids=()):
        self._datasets = datasets if datasets is not None else []
        self._fail_ids = set(fail_ids)
        self.deleted_ids = []

    def get_all(self, workspace_id):
        return self._datasets

    def delete(self, workspace_id, force_validation, dataset_id):
        if dataset_id in self._fail_ids:
            raise RuntimeError(f"boom-{dataset_id}")
        self.deleted_ids.append(dataset_id)
        return {"ok": True}


class _FakeWorkspaceService:
    def __init__(self, workspaces=None, delete_result="ok", raise_on_delete=False):
        self._workspaces = workspaces if workspaces is not None else []
        self._delete_result = delete_result
        self._raise_on_delete = raise_on_delete
        self.delete_called_with = None

    def get_all(self):
        return self._workspaces

    def delete(self, workspace_id, force_validation):
        if self._raise_on_delete:
            raise RuntimeError("boom-workspace")
        self.delete_called_with = workspace_id
        return self._delete_result


# ---------------------------------------------------------------------------
# _destroy_powerbi_datasets
# ---------------------------------------------------------------------------


def test_destroy_datasets_deletes_all():
    service = _FakeDatasetService(datasets=[{"id": "d1"}, {"id": "d2"}])
    assert pbh._destroy_powerbi_datasets(service, "ws1") is True
    assert service.deleted_ids == ["d1", "d2"]


def test_destroy_datasets_empty_is_noop_success():
    service = _FakeDatasetService(datasets=[])
    assert pbh._destroy_powerbi_datasets(service, "ws1") is True


def test_destroy_datasets_none_from_api_is_noop_success():
    service = _FakeDatasetService(datasets=None)
    assert pbh._destroy_powerbi_datasets(service, "ws1") is True


def test_destroy_datasets_partial_failure_returns_false_but_deletes_others():
    service = _FakeDatasetService(datasets=[{"id": "d1"}, {"id": "d2"}], fail_ids={"d1"})
    assert pbh._destroy_powerbi_datasets(service, "ws1") is False
    assert service.deleted_ids == ["d2"]


def test_destroy_datasets_skips_entries_without_id():
    service = _FakeDatasetService(datasets=[{"name": "no-id"}, {"id": "d2"}])
    assert pbh._destroy_powerbi_datasets(service, "ws1") is True
    assert service.deleted_ids == ["d2"]


# ---------------------------------------------------------------------------
# _destroy_powerbi_workspace
# ---------------------------------------------------------------------------


def test_destroy_workspace_deletes_when_present():
    service = _FakeWorkspaceService(workspaces=[{"id": "ws1"}, {"id": "ws2"}])
    assert pbh._destroy_powerbi_workspace(service, "ws1") is True
    assert service.delete_called_with == "ws1"


def test_destroy_workspace_already_deleted_is_idempotent_noop():
    service = _FakeWorkspaceService(workspaces=[{"id": "ws2"}])
    assert pbh._destroy_powerbi_workspace(service, "ws1") is True
    assert service.delete_called_with is None


def test_destroy_workspace_delete_returns_none_is_failure():
    service = _FakeWorkspaceService(workspaces=[{"id": "ws1"}], delete_result=None)
    assert pbh._destroy_powerbi_workspace(service, "ws1") is False


def test_destroy_workspace_delete_raises_is_failure():
    service = _FakeWorkspaceService(workspaces=[{"id": "ws1"}], raise_on_delete=True)
    assert pbh._destroy_powerbi_workspace(service, "ws1") is False


# ---------------------------------------------------------------------------
# destroy_powerbi_assets (end-to-end orchestration)
# ---------------------------------------------------------------------------


def test_destroy_powerbi_assets_noop_when_no_workspace_id(monkeypatch):
    monkeypatch.setattr(pbh.env, "get_variables", lambda: {"powerbi": {}})
    assert pbh.destroy_powerbi_assets({"services": {}}) is True


def test_destroy_powerbi_assets_noop_when_powerbi_key_missing(monkeypatch):
    monkeypatch.setattr(pbh.env, "get_variables", lambda: {})
    assert pbh.destroy_powerbi_assets({"services": {}}) is True


def test_destroy_powerbi_assets_fails_without_token(monkeypatch):
    monkeypatch.setattr(pbh.env, "get_variables", lambda: {"powerbi": {"workspace_id": "ws1"}})
    monkeypatch.setattr(pbh, "get_powerbi_token", lambda: None)
    assert pbh.destroy_powerbi_assets({"services": {}}) is False


def test_destroy_powerbi_assets_success_clears_variables(monkeypatch):
    monkeypatch.setattr(pbh.env, "get_variables", lambda: {"powerbi": {"workspace_id": "ws1", "reports": {"a": "1"}}})
    monkeypatch.setattr(pbh, "get_powerbi_token", lambda: "fake-token")
    monkeypatch.setattr(
        pbh, "AzurePowerBIDatasetService", lambda powerbi_token, state: _FakeDatasetService(datasets=[{"id": "d1"}])
    )
    monkeypatch.setattr(
        pbh,
        "AzurePowerBIWorkspaceService",
        lambda powerbi_token, state: _FakeWorkspaceService(workspaces=[{"id": "ws1"}]),
    )

    cleared = {}
    monkeypatch.setattr(pbh, "_clear_powerbi_variables", lambda: cleared.setdefault("called", True))

    assert pbh.destroy_powerbi_assets({"services": {}}) is True
    assert cleared.get("called") is True


def test_destroy_powerbi_assets_partial_failure_does_not_clear_variables(monkeypatch):
    monkeypatch.setattr(pbh.env, "get_variables", lambda: {"powerbi": {"workspace_id": "ws1"}})
    monkeypatch.setattr(pbh, "get_powerbi_token", lambda: "fake-token")
    monkeypatch.setattr(
        pbh,
        "AzurePowerBIDatasetService",
        lambda powerbi_token, state: _FakeDatasetService(datasets=[{"id": "d1"}], fail_ids={"d1"}),
    )
    monkeypatch.setattr(
        pbh,
        "AzurePowerBIWorkspaceService",
        lambda powerbi_token, state: _FakeWorkspaceService(workspaces=[{"id": "ws1"}]),
    )

    cleared = {}
    monkeypatch.setattr(pbh, "_clear_powerbi_variables", lambda: cleared.setdefault("called", True))

    assert pbh.destroy_powerbi_assets({"services": {}}) is False
    assert "called" not in cleared
