"""Tests of Babylon.core.destroy (planning only: pure functions, no network)."""

import pytest

from Babylon.core.destroy import DESTROY_ORDER, is_full_destroy, plan_destroy
from Babylon.core.errors import InvalidOptionsError
from Babylon.core.models import DestroyOptions
from Babylon.core.selection import resolve_resources


def make_state(org="o-1", sol="sol-1", ws="w-1", webapp="webapp-x", schema="s_1") -> dict:
    return {
        "services": {
            "api": {"organization_id": org, "solution_id": sol, "workspace_id": ws},
            "webapp": {"webapp_name": webapp},
            "postgres": {"schema_name": schema},
        }
    }


def test_full_plan_keeps_historical_order_and_ids():
    plan = plan_destroy(make_state(), resolve_resources())
    assert [(t.resource, t.resource_id) for t in plan] == [
        ("solution", "sol-1"),
        ("workspace", "w-1"),
        ("organization", "o-1"),
        ("webapp", "webapp-x"),
    ]
    assert [t.resource for t in plan] == list(DESTROY_ORDER)


def test_build_is_never_destroyed():
    assert plan_destroy(make_state(), {"build"}) == []


@pytest.mark.parametrize(
    "include, exclude, expected",
    [
        (("workspace",), (), ["workspace"]),
        (("organization", "solution", "workspace"), (), ["solution", "workspace", "organization"]),  # order from DESTROY_ORDER
        ((), ("webapp",), ["solution", "workspace", "organization"]),
    ],
)
def test_plan_respects_selection(include, exclude, expected):
    plan = plan_destroy(make_state(), resolve_resources(include, exclude))
    assert [t.resource for t in plan] == expected


def test_not_deployed_resources_stay_in_plan_without_id():
    plan = plan_destroy(make_state(sol="", webapp=None), resolve_resources())
    deployed = {t.resource: t.deployed for t in plan}
    assert deployed == {"solution": False, "workspace": True, "organization": True, "webapp": False}
    assert plan[0].resource_id is None


@pytest.mark.parametrize("state", [{}, {"services": {}}, {"services": {"api": None}}, None])
def test_plan_tolerates_empty_or_partial_state(state):
    plan = plan_destroy(state, resolve_resources())
    assert len(plan) == 4
    assert not any(t.deployed for t in plan)


def test_is_full_destroy():
    assert not is_full_destroy(make_state())
    assert is_full_destroy(make_state(org="", sol="", ws="", webapp="", schema=""))
    assert not is_full_destroy(make_state(org="", sol="", ws="", webapp=""))  # schema still there
    assert is_full_destroy({})


def test_destroy_options_defaults():
    opts = DestroyOptions(context="c", tenant="t", variable_files=())
    assert (opts.include, opts.exclude, opts.fail_fast) == ((), (), True)


@pytest.mark.parametrize(
    "include, exclude, kept",
    [
        ((), ("workspace",), "workspace"),  # org + solution deleted, workspace orphaned
        (("organization",), (), "solution, workspace"),
        (("solution",), (), "workspace"),
    ],
)
def test_destroying_a_parent_while_keeping_a_deployed_child_is_refused(include, exclude, kept):
    with pytest.raises(InvalidOptionsError, match=f"while keeping {kept}"):
        plan_destroy(make_state(), resolve_resources(include, exclude))


@pytest.mark.parametrize(
    "include, exclude, state",
    [
        (("workspace",), (), make_state()),  # child alone: always fine
        ((), ("organization",), make_state()),  # keep the parent, delete children
        (("solution",), (), make_state(ws="")),  # workspace not deployed: nothing orphaned
        (("organization",), (), make_state(sol="", ws="")),
    ],
)
def test_allowed_partial_destroys(include, exclude, state):
    plan_destroy(state, resolve_resources(include, exclude))  # no error
