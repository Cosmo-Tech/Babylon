"""Typed inputs and outputs of the programmatic Babylon operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


@dataclass(frozen=True)
class ApplyOptions:
    """Everything `apply` needs, passed explicitly (equivalent of `babylon apply` options).

    Attributes:
        deploy_dir: directory containing the Babylon YAML manifests (the CLI `DEPLOY_DIR`).
        context: Babylon context id (`-c`), used to isolate the state.
        tenant: Babylon tenant (`-t`), also the Kubernetes namespace of the platform.
        variable_files: variable files (`--var-file`), merged together.
        include / exclude: resource selection (`--include` / `--exclude`).
        fail_fast: stop at the first failure; remaining manifests are SKIPPED.
    """

    deploy_dir: Path
    context: str
    tenant: str
    variable_files: tuple[Path, ...]
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    fail_fast: bool = True


@dataclass(frozen=True)
class DestroyOptions:
    """Everything `destroy` needs (equivalent of `babylon destroy` options).

    No deploy_dir: destroy works only from the state (context + tenant), not from YAML files.
    """

    context: str
    tenant: str
    variable_files: tuple[Path, ...]
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    fail_fast: bool = True


class ResourceStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ResourceOutcome:
    """What happened to one manifest file."""

    resource: str  # "organization", "solution", ...
    file: str  # file name, e.g. "Organization.yaml"
    status: ResourceStatus
    error: str | None = None


@dataclass
class ApplyResult:
    context: str
    tenant: str
    resources: list[ResourceOutcome] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        """True only if every manifest was deployed successfully."""
        return all(r.status == ResourceStatus.SUCCEEDED for r in self.resources)
