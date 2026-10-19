"""Reading the Babylon manifests of a deployment directory (no click, no network)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from yaml import YAMLError, safe_dump, safe_load

from Babylon.core.errors import InvalidOptionsError

# `kind:` value in a manifest  ->  resource name used by include/exclude.
KIND_TO_RESOURCE: dict[str, str] = {
    "Build": "build",
    "Organization": "organization",
    "Solution": "solution",
    "Webapp": "webapp",
    "Workspace": "workspace",
}

# Deployment order of `babylon apply` (a solution needs its organization, etc.).
APPLY_ORDER: tuple[str, ...] = ("build", "organization", "solution", "webapp", "workspace")


@dataclass(frozen=True)
class Manifest:
    resource: str  # "organization", "solution", ...
    path: Path
    namespace: str
    content: str  # file content with `{{ x }}` rewritten as `${ x }` (Mako syntax)


def _to_mako(text: str) -> str:
    """Babylon manifests use `{{ var }}`; the templating engine (Mako) expects `${ var }`."""
    return text.replace("{{", "${").replace("}}", "}")


def load_manifest(path: Path) -> Manifest | None:
    """Parse one file. Returns None when its `kind` is not a Babylon resource.

    Raises:
        InvalidOptionsError: the file is not valid YAML or is not a YAML mapping.
    """
    content = _to_mako(path.read_text(encoding="utf-8"))
    try:
        data = safe_load(content)
    except YAMLError as exc:
        raise InvalidOptionsError(f"{path.name} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidOptionsError(f"{path.name} must be a YAML mapping with a 'kind' key")

    resource = KIND_TO_RESOURCE.get(data.get("kind"))
    if resource is None:
        return None
    return Manifest(resource=resource, path=path, namespace=safe_dump(data.get("namespace")), content=content)


def load_manifests(deploy_dir: Path) -> list[Manifest]:
    """Load every `*.yaml` / `*.yml` file at the top level of `deploy_dir`, in file-name order.

    Raises:
        InvalidOptionsError: `deploy_dir` is not a directory, or a file cannot be parsed.
    """
    deploy_dir = Path(deploy_dir)
    if not deploy_dir.is_dir():
        raise InvalidOptionsError(f"Deployment directory not found: {deploy_dir}")
    files = sorted(p for p in deploy_dir.iterdir() if p.is_file() and p.suffix in (".yaml", ".yml"))
    return [m for m in (load_manifest(f) for f in files) if m is not None]


def plan_apply(manifests: Iterable[Manifest], selected: Iterable[str]) -> list[Manifest]:
    """Return the manifests to deploy, filtered by `selected` and sorted in APPLY_ORDER."""
    selected = set(selected)
    manifests = list(manifests)
    return [m for resource in APPLY_ORDER if resource in selected for m in manifests if m.resource == resource]
