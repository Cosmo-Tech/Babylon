"""Planning of destroy: which resources to delete, in which order.

Destroy works only from the state: the state tells which ids exist, the selection
(include/exclude) tells which of them the user wants to delete.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from Babylon.core.errors import InvalidOptionsError

# Same order as the CLI (_execute_destroy): children before their organization.
# "build" is not here: there is nothing to destroy for it.
DESTROY_ORDER = ("solution", "workspace", "organization", "webapp")

# resource -> (label shown to the user, state section, state key holding the id)
_STATE_KEYS = {
    "organization": ("Organization", "api", "organization_id"),
    "solution": ("Solution", "api", "solution_id"),
    "workspace": ("Workspace", "api", "workspace_id"),
    "webapp": ("Web App", "webapp", "webapp_name"),
}


@dataclass(frozen=True)
class DestroyTarget:
    """One resource selected for destruction."""

    resource: str  # "solution", "workspace", ...
    label: str  # "Solution", "Web App", ... (for messages)
    resource_id: str | None  # id from the state, None if not deployed

    @property
    def deployed(self) -> bool:
        return bool(self.resource_id)


def _services(state: dict) -> dict:
    return (state or {}).get("services") or {}


def plan_destroy(state: dict, selected: Iterable[str]) -> list[DestroyTarget]:
    """Return the selected resources in destroy order, with their id from the state.

    Resources that are not deployed are kept in the plan (resource_id=None) so the
    caller can report them as SKIPPED instead of silently ignoring them.
    """
    selected = set(selected)
    plan = [
        DestroyTarget(resource, _STATE_KEYS[resource][0], resource_id(state, resource))
        for resource in DESTROY_ORDER
        if resource in selected
    ]
    _check_no_orphans(state, plan)
    return plan


# parent -> children that reference it (a workspace points to its solution and organization)
_CHILDREN = {
    "organization": ("solution", "workspace"),
    "solution": ("workspace",),
}


def _check_no_orphans(state: dict, plan: list[DestroyTarget]) -> None:
    """Refuse to destroy a parent while a deployed child is kept (it would be orphaned).

    Example: `--exclude workspace` would delete the organization and the solution
    but keep a workspace pointing to them.
    """
    targeted = {t.resource for t in plan}
    for target in plan:
        if not target.deployed:
            continue
        kept = [child for child in _CHILDREN.get(target.resource, ()) if child not in targeted and resource_id(state, child)]
        if kept:
            raise InvalidOptionsError(
                f"Cannot destroy {target.resource} while keeping {', '.join(kept)}: "
                f"they depend on it. Also destroy {', '.join(kept)} or keep {target.resource}."
            )


def resource_id(state: dict, resource: str) -> str | None:
    """Id of resource in the state, or None if not deployed."""
    _, section, key = _STATE_KEYS[resource]
    return (_services(state).get(section) or {}).get(key) or None


def is_full_destroy(state: dict) -> bool:
    """True when every tracked resource id has been cleared from the state."""
    services = _services(state)
    api_ids = services.get("api") or {}
    return (
        not api_ids.get("organization_id")
        and not api_ids.get("solution_id")
        and not api_ids.get("workspace_id")
        and not (services.get("webapp") or {}).get("webapp_name")
        and not (services.get("postgres") or {}).get("schema_name")
    )
