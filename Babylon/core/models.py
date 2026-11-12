"""Typed inputs and outputs of the Babylon operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


@dataclass(frozen=True)
class ApplyOptions:
    """Options required to run a Babylon apply operation.

    Attributes:
        deploy_dir: directory containing the YAML manifests.
        context: Babylon context id (-c), used to isolate the state.
        tenant: Babylon tenant (-t), also the Kubernetes namespace.
        variable_files: variable files to load and merge (--var-file).
        include / exclude: resources to include or exclude.
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
    """Options required to run a Babylon destroy operation.

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
        return all(resource.status == ResourceStatus.SUCCEEDED for resource in self.resources)


@dataclass
class DestroyOutcome:
    """What happened to one resource during destroy."""

    resource: str  # "solution", "workspace", ...
    resource_id: str | None  # id from the state before destroy (None: not deployed)
    status: ResourceStatus
    error: str | None = None


@dataclass
class DestroyResult:
    context: str
    tenant: str
    resources: list[DestroyOutcome] = field(default_factory=list)
    cancelled: bool = False  # the confirmation was refused: nothing was touched
    nothing_to_destroy: bool = False  # no selected resource is deployed: nothing was asked nor touched
    state: dict = field(default_factory=dict)  # state after destroy (for the summary)

    @property
    def succeeded(self) -> bool:
        """True if nothing failed (not-deployed resources are SKIPPED, which is fine)."""
        return not self.cancelled and all(resource.status != ResourceStatus.FAILED for resource in self.resources)
