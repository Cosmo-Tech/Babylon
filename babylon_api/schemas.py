"""Request/response bodies of the Babylon API (validated by pydantic before any work starts).

Every field coming from the network is untrusted: it will later become a git argument,
a path on disk, a Kubernetes namespace or a Secret name. The rules below reject bad
values with HTTP 422 instead of letting them reach git, the filesystem or the cluster.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Annotated, ClassVar, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from Babylon.core.selection import ALLOWED_RESOURCES, resolve_resources

# Kubernetes name (RFC 1123 label): lowercase letters, digits and '-', not at the ends.
# The tenant IS a namespace, and both end up in the state Secret "babylon-state-<context>-<tenant>".
_K8S_NAME = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")

# Git branch/tag/sha. Must not start with '-' (would be read as a git option) and no '..'.
_GIT_REF = re.compile(r"^[A-Za-z0-9._/][A-Za-z0-9._/-]*$")


def _k8s_name(value: str) -> str:
    if not _K8S_NAME.match(value):
        raise ValueError("must contain only lowercase letters, digits and '-', and start/end with a letter or digit")
    return value


def _repo_path(value: str) -> str:
    """A relative path that stays inside the cloned repository."""
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise ValueError("must be a relative path inside the repository (no leading '/', no '..')")
    return str(path)


K8sName = Annotated[str, Field(max_length=40), AfterValidator(_k8s_name)]
RepoPath = Annotated[str, Field(max_length=255), AfterValidator(_repo_path)]


class Repository(BaseModel):
    """Where the deployment files live (cloned by the worker)."""

    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    ref: str = Field(default="main", max_length=255)

    @field_validator("url")
    @classmethod
    def _https_only(cls, url: HttpUrl) -> HttpUrl:
        if url.scheme != "https":
            raise ValueError("only https:// repositories are allowed")
        return url

    @field_validator("ref")
    @classmethod
    def _safe_ref(cls, ref: str) -> str:
        if not _GIT_REF.match(ref) or ".." in ref:
            raise ValueError("invalid git ref")
        return ref


# Resources the API manages. Narrower than the CLI on purpose (v1):
# - webapp: Terraform, not handled by the API;
# - workspace: in-cluster PostgreSQL (Superset) only, see the worker.
API_RESOURCES: tuple[str, ...] = tuple(r for r in ALLOWED_RESOURCES if r != "webapp")


TENANT_INJECTED_MESSAGE = "The tenant is automatically injected by the backend and must not be provided by the client."


class _OperationRequest(BaseModel):
    """Fields shared by apply and destroy."""

    model_config = ConfigDict(extra="forbid")  # a typo like "exlude" is an error, not silently ignored

    # The tenant is the namespace the API runs in (one Babylon API per tenant namespace).
    # Public requests must not carry it; the internal Job payloads (ApplyJob/DestroyJob) do.
    _tenant_from_client: ClassVar[bool] = False

    context: K8sName
    include: list[str] = Field(default_factory=list, description=f"Allowed: {', '.join(API_RESOURCES)}")
    exclude: list[str] = Field(default_factory=list, description=f"Allowed: {', '.join(API_RESOURCES)}")

    @model_validator(mode="before")
    @classmethod
    def _no_client_tenant(cls, data):
        # Explicit message instead of the generic "Extra inputs are not permitted".
        if not cls._tenant_from_client and isinstance(data, dict) and "tenant" in data:
            raise ValueError(TENANT_INJECTED_MESSAGE)
        return data

    @model_validator(mode="after")
    def _valid_selection(self):
        resolve_resources(tuple(self.include), tuple(self.exclude))
        unsupported = [r for r in self.include + self.exclude if r not in API_RESOURCES]
        if unsupported:
            raise ValueError(f"Not supported by Babylon API: {', '.join(unsupported)}. Allowed: {', '.join(API_RESOURCES)}")
        return self

    @property
    def resources(self) -> tuple[str, ...]:
        """The selection as an explicit list, never containing webapp (given to the core as `include`)."""
        selected = resolve_resources(tuple(self.include), tuple(self.exclude))
        return tuple(r for r in API_RESOURCES if r in selected)


class ApplyRequest(_OperationRequest):
    repository: Repository
    deploy_dir: RepoPath = Field(description="Directory of the Babylon YAML files, relative to the repository root")
    variable_files: list[RepoPath] = Field(default_factory=lambda: ["variables.yaml"], min_length=1, max_length=10)


class DestroyRequest(_OperationRequest):
    """No repository: destroy works from the state Secret (babylon-state-<context>-<tenant>) only."""

    # Destroy is irreversible and there is no prompt over HTTP: the caller must say it explicitly.
    confirm: Literal[True] = Field(description="Must be true: destroy cannot be undone")


# Internal payloads: what the API puts in the Job (BABYLON_OPERATION) and the worker validates.
# Same fields as the public requests + the tenant injected by the API (its own namespace).


class ApplyJob(ApplyRequest):
    _tenant_from_client: ClassVar[bool] = True
    tenant: K8sName


class DestroyJob(DestroyRequest):
    _tenant_from_client: ClassVar[bool] = True
    tenant: K8sName


class OperationAccepted(BaseModel):
    """The operation was submitted as a Kubernetes Job; poll GET /operations/{operation_id}."""

    operation_id: str
    operation: Literal["apply", "destroy"]
    tenant: str = Field(description="Namespace of the API, injected as tenant")
    status: Literal["pending"] = "pending"
    job_name: str


class OperationStatus(BaseModel):
    operation_id: str
    operation: str | None
    context: str | None
    tenant: str | None
    status: Literal["pending", "running", "succeeded", "failed"]
    job_name: str
    created_at: datetime | None = None
    result: dict | None = Field(default=None, description="Summary written by the worker when the Job is finished")
