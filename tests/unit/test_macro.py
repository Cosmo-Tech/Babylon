import pytest
from click import Abort
from cosmotech_api.models.organization_access_control import OrganizationAccessControl
from cosmotech_api.models.solution_access_control import SolutionAccessControl
from cosmotech_api.models.workspace_access_control import WorkspaceAccessControl

from Babylon.commands.macro.deploy import diff, resolve_inclusion_exclusion


def test_organization_diff():
    acl1 = [
        OrganizationAccessControl.from_dict({"id": "toto@cosmotech.com", "role": "reader"}),
        OrganizationAccessControl.from_dict({"id": "tata@cosmotech.com", "role": "writer"}),
    ]
    acl2 = [
        OrganizationAccessControl.from_dict({"id": "toto@cosmotech.com", "role": "admin"}),  # updated
        OrganizationAccessControl.from_dict({"id": "titi@cosmotech.com", "role": "reader"}),  # added
    ]
    to_add, to_delete, to_update = diff(acl1, acl2)
    assert to_add[0] == "titi@cosmotech.com"
    assert to_delete[0] == "tata@cosmotech.com"
    assert to_update[0] == "toto@cosmotech.com"


def test_workspace_diff():
    acl1 = [
        WorkspaceAccessControl.from_dict({"id": "toto@cosmotech.com", "role": "reader"}),
        WorkspaceAccessControl.from_dict({"id": "tata@cosmotech.com", "role": "writer"}),
    ]
    acl2 = [
        WorkspaceAccessControl.from_dict({"id": "toto@cosmotech.com", "role": "admin"}),  # updated
        WorkspaceAccessControl.from_dict({"id": "titi@cosmotech.com", "role": "reader"}),  # added
    ]
    to_add, to_delete, to_update = diff(acl1, acl2)
    assert to_add[0] == "titi@cosmotech.com"
    assert to_delete[0] == "tata@cosmotech.com"
    assert to_update[0] == "toto@cosmotech.com"


def test_solution_diff():
    acl1 = [
        SolutionAccessControl.from_dict({"id": "toto@cosmotech.com", "role": "reader"}),
        SolutionAccessControl.from_dict({"id": "tata@cosmotech.com", "role": "writer"}),
    ]
    acl2 = [
        SolutionAccessControl.from_dict({"id": "toto@cosmotech.com", "role": "admin"}),  # updated
        SolutionAccessControl.from_dict({"id": "titi@cosmotech.com", "role": "reader"}),  # added
    ]
    to_add, to_delete, to_update = diff(acl1, acl2)
    assert to_add[0] == "titi@cosmotech.com"
    assert to_delete[0] == "tata@cosmotech.com"
    assert to_update[0] == "toto@cosmotech.com"


def test_resolve_inclusion_exclusion_no_filters():
    assert resolve_inclusion_exclusion(include=(), exclude=()) == (True, True, True, True)


def test_resolve_inclusion_exclusion_include_all_valid():
    assert resolve_inclusion_exclusion(include=("organization", "solution", "workspace", "webapp"), exclude=()) == (
        True,
        True,
        True,
        True,
    )


def test_resolve_inclusion_exclusion_exclude_all_valid():
    assert resolve_inclusion_exclusion(include=(), exclude=("organization", "solution", "workspace", "webapp")) == (
        False,
        False,
        False,
        False,
    )


def test_resolve_inclusion_exclusion_include_duplicates():
    assert resolve_inclusion_exclusion(include=("organization", "organization"), exclude=()) == (
        True,
        False,
        False,
        False,
    )


def test_resolve_inclusion_exclusion_invalid_exclude():
    with pytest.raises(Abort):
        resolve_inclusion_exclusion(include=(), exclude=("invalid",))


def test_resolve_inclusion_exclusion_partial_include_mixed():
    with pytest.raises(Abort):
        resolve_inclusion_exclusion(include=("organization", "invalid"), exclude=())


def test_resolve_inclusion_exclusion_partial_exclude_mixed():
    with pytest.raises(Abort):
        resolve_inclusion_exclusion(include=(), exclude=("workspace", "invalid"))


def test_resolve_inclusion_exclusion_conflicting_filters_variation():
    with pytest.raises(Abort):
        resolve_inclusion_exclusion(include=("solution", "workspace"), exclude=("organization",))
