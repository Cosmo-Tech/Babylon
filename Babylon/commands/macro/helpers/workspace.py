"""
Helpers for workspace deployment and teardown, organised by concern:

  1. Cosmotech API  — create / update workspace + security sync
                    — generic API resource deletion (used by destroy)
  2. Kubernetes resources  — Secret and ConfigMap lifecycle (create / delete)
  3. Kubernetes PostgreSQL — service discovery + schema init-job orchestration
                           — schema teardown (used by destroy)
  4. Superset           — sequential component import + Workspace.yaml ID feedback loop
  5. PowerBI            — report publish + Workspace.yaml ID feedback loop
"""


import subprocess
from re import compile, MULTILINE, IGNORECASE
from tempfile import mkdtemp
from zipfile import ZipFile
from base64 import b64encode
from logging import getLogger
from pathlib import Path
from string import Template
from textwrap import dedent
from typing import Callable
from pathlib import Path
# from ruamel.yaml import YAML
from io import BytesIO
from shutil import rmtree
import uuid as _uuid_mod

import requests


from cosmotech_api.models.workspace_create_request import WorkspaceCreateRequest
from cosmotech_api.models.workspace_security import WorkspaceSecurity
from cosmotech_api.models.workspace_update_request import WorkspaceUpdateRequest
from kubernetes import client, config, utils
from kubernetes import config as kube_config
from kubernetes.utils import FailToCreateError
from yaml import safe_load

from Babylon.utils.credentials import get_superset_token
from Babylon.commands.macro.helpers.common import update_object_security
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


# ---------------------------------------------------------------------------
# Cosmotech API helpers
# ---------------------------------------------------------------------------


def create_workspace(api_instance, api_section: dict, payload: dict, state: dict) -> bool:
    """Create a new workspace and persist its ID in state. Returns False on failure."""
    logger.info("  [dim]→ No existing workspace ID found. Creating...[/dim]")
    workspace = api_instance.create_workspace(
        organization_id=api_section["organization_id"],
        workspace_create_request=WorkspaceCreateRequest.from_dict(payload),
    )
    if workspace is None:
        logger.error("  [bold red]✘[/bold red] Failed to create workspace")
        return False
    logger.info(f"  [bold green]✔[/bold green] Workspace [bold magenta]{workspace.id}[/bold magenta] created")
    state["services"]["api"]["workspace_id"] = workspace.id
    return True


def sync_workspace_security(api_instance, api_section: dict, payload: dict) -> bool:
    """Synchronise security roles if a security block is present in the payload."""
    if not payload.get("security"):
        return True
    try:
        logger.info("  [dim]→ Syncing security policies...[/dim]")
        current_security = api_instance.get_workspace_security(
            organization_id=api_section["organization_id"], workspace_id=api_section["workspace_id"]
        )
        update_object_security(
            "workspace",
            current_security=current_security,
            desired_security=WorkspaceSecurity.from_dict(payload.get("security")),
            api_instance=api_instance,
            object_id=[api_section["organization_id"], api_section["workspace_id"]],
        )
        return True
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Security update failed: {e}")
        return False


def update_workspace(api_instance, api_section: dict, payload: dict) -> bool:
    """Update an existing workspace and sync its security policy. Returns False on failure."""
    logger.info(f"  [dim]→ Existing ID [bold cyan]{api_section['workspace_id']}[/bold cyan] found. Updating...[/dim]")
    updated = api_instance.update_workspace(
        organization_id=api_section["organization_id"],
        workspace_id=api_section["workspace_id"],
        workspace_update_request=WorkspaceUpdateRequest.from_dict(payload),
    )
    if updated is None:
        logger.error(f"  [bold red]✘[/bold red] Failed to update workspace {api_section['workspace_id']}")
        return False
    if not sync_workspace_security(api_instance, api_section, payload):
        return False
    logger.info(f"  [bold green]✔[/bold green] Workspace [bold magenta]{api_section['workspace_id']}[/bold magenta] updated")
    return True


def delete_api_resource(
    api_call: Callable[..., None], resource_name: str, org_id: str | None, resource_id: str, state: dict, state_key: str
) -> None:
    """Delete a Cosmotech API resource and clear its ID from state.

    Handles the repetitive deletion pattern shared across organization, solution
    and workspace teardown.  A 404 response is treated as a no-op (already gone).
    """
    if not resource_id:
        logger.warning(f"  [yellow]⚠[/yellow] [dim]No {resource_name} ID found in state! skipping deletion[dim]")
        return

    try:
        logger.info(f"  [dim]→ Existing ID [bold cyan]{resource_id}[/bold cyan] found. Deleting...[/dim]")
        if org_id and resource_name != "Organization":
            api_call(organization_id=org_id, **{f"{resource_name.lower()}_id": resource_id})
        else:
            api_call(organization_id=resource_id)

        logger.info(f"  [bold green]✔[/bold green] {resource_name} [magenta]{resource_id}[/magenta] deleted")
        state["services"]["api"][state_key] = ""
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "Not Found" in error_msg:
            logger.info(f"  [bold yellow]⚠[/bold yellow] {resource_name} [magenta]{resource_id}[/magenta] already deleted (404)")
            state["services"]["api"][state_key] = ""
        else:
            logger.error(f"  [bold red]✘[/bold red] Error deleting {resource_name.lower()} {resource_id} reason: {e}")


# ---------------------------------------------------------------------------
# Kubernetes Secret and ConfigMap lifecycle
# ---------------------------------------------------------------------------


def create_workspace_secret(
    namespace: str,
    organization_id: str,
    workspace_id: str,
    writer_password: str,
) -> bool:
    """Create a Kubernetes Secret for a workspace containing API and PostgreSQL credentials.

    The secret is named ``<organization_id>-<workspace_id>`` and holds all
    environment variables required by workspace.

    Returns:
        bool: True if the secret was created or already exists, False on error.
    """
    secret_name = f"{organization_id}-{workspace_id}"
    data = {
        "POSTGRES_USER_PASSWORD": writer_password,
    }
    encoded_data = {k: b64encode(v.encode("utf-8")).decode("utf-8") for k, v in data.items()}

    secret = client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(name=secret_name, namespace=namespace),
        type="Opaque",
        data=encoded_data,
    )

    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        v1.create_namespaced_secret(namespace=namespace, body=secret)
        logger.info(f"  [bold green]✔[/bold green] Secret [magenta]{secret_name}[/magenta] created")
        return True
    except client.exceptions.ApiException as e:
        if getattr(e, "status", None) == 409:
            logger.warning(f"  [yellow]⚠[/yellow] [dim]Secret [magenta]{secret_name}[/magenta] already exists[/dim]")
            return True
        logger.error(f"  [bold red]✘[/bold red] Failed to create secret {secret_name}: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error creating secret {secret_name}")
        logger.debug(f"  Detail: {e}", exc_info=True)
        return False


def create_coal_configmap(
    namespace: str,
    organization_id: str,
    workspace_id: str,
    db_host: str,
    db_port: str,
    db_name: str,
    schema_name: str,
    writer_username: str,
) -> bool:
    """Create a CoAL ConfigMap for a workspace.

    The ConfigMap is named ``<organization_id>-<workspace_id>-coal-config`` and
    contains a ``coal-config.toml`` key with Postgres output configuration.  The
    ``user_password`` value is deliberately set to the literal string
    ``env.POSTGRES_USER_PASSWORD`` so that the CoAL runtime resolves it from the
    environment at execution time.

    Returns:
        bool: True if the ConfigMap was created or already exists, False on error.
    """
    configmap_name = f"{organization_id}-{workspace_id}-coal-config"
    coal_toml = dedent(f"""\
        [[outputs]]
        type = "postgres"
        [outputs.conf.postgres]
        host = "{db_host}"
        port = "{db_port}"
        db_name = "{db_name}"
        db_schema = "{schema_name}"
        user_name = "{writer_username}"
        user_password = "env.POSTGRES_USER_PASSWORD"
    """)

    configmap = client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(name=configmap_name, namespace=namespace),
        data={"coal-config.toml": coal_toml},
    )

    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        v1.create_namespaced_config_map(namespace=namespace, body=configmap)
        logger.info(f"  [bold green]✔[/bold green] ConfigMap [magenta]{configmap_name}[/magenta] created")
        return True
    except client.ApiException as e:
        if e.status == 409:
            logger.warning(f"  [yellow]⚠[/yellow] [dim]ConfigMap [magenta]{configmap_name}[/magenta] already exists[/dim]")
            return True
        logger.error(f"  [bold red]✘[/bold red] Failed to create ConfigMap {configmap_name}: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error creating ConfigMap {configmap_name}")
        logger.debug(f"  Detail: {e}", exc_info=True)
        return False


def delete_kubernetes_resources(namespace: str, organization_id: str, workspace_id: str) -> None:
    """Delete the Workspace Secret and CoAL ConfigMap created during deployment.

    Targets:
      - Secret:    ``<organization_id>-<workspace_id>``
      - ConfigMap: ``<organization_id>-<workspace_id>-coal-config``

    If a resource is already gone (404), a warning is logged and execution
    continues without error.
    """
    secret_name = f"{organization_id}-{workspace_id}"
    configmap_name = f"{organization_id}-{workspace_id}-coal-config"

    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
    except Exception as e:
        logger.error("  [bold red]✘[/bold red] Failed to initialise Kubernetes client")
        logger.debug(f"  Detail: {e}", exc_info=True)
        return

    # --- Delete Secret ---
    try:
        logger.info("  [dim]→ Deleting workspace Secret ...[/dim]")
        v1.delete_namespaced_secret(name=secret_name, namespace=namespace)
        logger.info(f"  [bold green]✔[/bold green] Secret [magenta]{secret_name}[/magenta] deleted")
    except client.ApiException as e:
        if e.status == 404:
            logger.warning("  [yellow]⚠[/yellow] [dim]Secret not found (already deleted)[/dim]")
        else:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete secret {secret_name}: {e.reason}")
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error deleting secret {secret_name}")
        logger.debug(f"  Detail: {e}", exc_info=True)

    # --- Delete ConfigMap ---
    try:
        logger.info("  [dim]→ Deleting workspace ConfigMap ...[/dim]")
        v1.delete_namespaced_config_map(name=configmap_name, namespace=namespace)
        logger.info(f"  [bold green]✔[/bold green] ConfigMap [magenta]{configmap_name}[/magenta] deleted")
    except client.ApiException as e:
        if e.status == 404:
            logger.warning("  [yellow]⚠[/yellow] [dim]ConfigMap not found (already deleted)[/dim]")
        else:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete ConfigMap {configmap_name}: {e.reason}")
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error deleting ConfigMap {configmap_name}")
        logger.debug(f"  Detail: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# Kubernetes PostgreSQL service discovery
# ---------------------------------------------------------------------------


def get_postgres_service_host(namespace: str) -> str:
    """Discover the PostgreSQL service name in a namespace to build its FQDN.

    Note: This function assumes PostgreSQL is running within the same Kubernetes cluster.
    External database clusters are not currently supported.
    """
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        services = v1.list_namespaced_service(namespace)

        for svc in services.items:
            labels = svc.metadata.labels or {}
            if "postgresql" in svc.metadata.name or labels.get("app.kubernetes.io/name") == "postgresql":
                logger.debug(f"  [dim]→ Found PostgreSQL service {svc.metadata.name}[/dim]")
                return f"{svc.metadata.name}.{namespace}.svc.cluster.local"

        return f"postgresql.{namespace}.svc.cluster.local"
    except Exception as e:
        logger.warning("  [bold yellow]⚠[/bold yellow] Service discovery failed ! default will be used.")
        logger.debug(f"  Exception details: {e}", exc_info=True)
        return f"postgresql.{namespace}.svc.cluster.local"


# ---------------------------------------------------------------------------
# Kubernetes PostgreSQL schema init-job orchestration
# ---------------------------------------------------------------------------


def _handle_init_job_logs(k8s_job_name: str, schema_name: str, state: dict) -> None:
    """Fetch init-job logs and update state based on their content."""
    logs_process = subprocess.run(
        ["kubectl", "logs", f"job/{k8s_job_name}", "-n", env.environ_id],
        capture_output=True,
        text=True,
    )
    if logs_process.returncode != 0:
        logger.error(f" [bold red]✘[/bold red] Failed to retrieve logs for job {k8s_job_name}")
        logger.debug(f" [bold red]✘[/bold red] Logs retrieval output {logs_process.stdout} {logs_process.stderr}")
        return

    job_logs = logs_process.stdout or logs_process.stderr
    if "ERROR" in job_logs or "error" in job_logs:
        logger.error("  [bold red]✘[/bold red] Schema creation failed inside the container")
        logger.debug(f"  [bold red]✘[/bold red] Job logs : {job_logs}")
    elif "already exists" in job_logs:
        logger.info(f"  [yellow]⚠[/yellow] [dim]Schema [magenta]{schema_name}[/magenta] already exists (skipping creation)[/dim]")
    else:
        logger.info(f"  [green]✔[/green] Schema creation [magenta]{schema_name}[/magenta] completed successfully")
        state["services"]["postgres"]["schema_name"] = schema_name


def _wait_and_check_init_job(k8s_job_name: str, schema_name: str, state: dict) -> None:
    """Wait for the init job to complete, then inspect its logs."""
    logger.info(f"  [dim]→ Waiting for job [cyan]{k8s_job_name}[/cyan] to complete...[/dim]")
    wait_process = subprocess.run(
        ["kubectl", "wait", "--for=condition=complete", "job", k8s_job_name, f"--namespace={env.environ_id}", "--timeout=50s"],
        capture_output=True,
        text=True,
    )
    if wait_process.returncode != 0:
        logger.error(f"  [bold red]✘[/bold red] Job {k8s_job_name} did not complete successfully see babylon logs for details")
        logger.debug(f"  [bold red]✘[/bold red] Job wait output {wait_process.stdout} {wait_process.stderr}")
        return
    logger.info("  [dim]→ Checking job logs for errors...[/dim]")
    _handle_init_job_logs(k8s_job_name, schema_name, state)


def _run_schema_init_job(script_path: Path, mapping: dict, workspace_id: str, schema_name: str, state: dict) -> None:
    """Apply a single K8s init job from *script_path* and wait for its outcome."""
    k8s_job_name = f"postgresql-init-{workspace_id}"
    kube_config.load_kube_config()
    k8s_client = client.ApiClient()

    with open(script_path, "r") as f:
        raw_content = f.read()

    yaml_dict = safe_load(Template(raw_content).safe_substitute(mapping))
    try:
        utils.create_from_dict(k8s_client, yaml_dict, namespace=env.environ_id)
        _wait_and_check_init_job(k8s_job_name, schema_name, state)
    except FailToCreateError as e:
        for inner_exception in e.api_exceptions:
            if inner_exception.status == 409:
                logger.warning(f"  [yellow]⚠[/yellow] [dim]Job [cyan]{k8s_job_name}[/cyan] already exists.[/dim]")
            else:
                logger.error(f"  [bold red]✘[/bold red] K8s Error ({inner_exception.status}): {inner_exception.reason}")
                logger.debug(f"  Detail: {inner_exception.body}")
    except Exception as e:
        logger.error("  [bold red]✘[/bold red] Unexpected error please check babylon logs file for details")
        logger.debug(f"  [bold red]✘[/bold red] {e}")


def deploy_postgres_schema(workspace_id: str, schema_config: dict, api_section: dict, deploy_dir: Path, state: dict) -> None:
    """Initialise the PostgreSQL schema and create the associated K8s resources."""
    db_host = get_postgres_service_host(env.environ_id)
    logger.info(f"  [dim]→ Initializing PostgreSQL schema for workspace [bold cyan]{workspace_id}[/bold cyan]...[/dim]")

    pg_config = env.get_config_from_k8s_secret_by_tenant("postgresql-config", env.environ_id)
    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    if not pg_config or not api_config:
        return

    schema_name = workspace_id.replace("-", "_")
    mapping = {
        "namespace": env.environ_id,
        "db_host": db_host,
        "db_port": "5432",
        "cosmotech_api_database": api_config.get("database-name", ""),
        "cosmotech_api_admin_username": api_config.get("admin-username", ""),
        "cosmotech_api_admin_password": api_config.get("admin-password", ""),
        "cosmotech_api_writer_username": api_config.get("writer-username", ""),
        "cosmotech_api_reader_username": api_config.get("reader-username", ""),
        "workspace_schema": schema_name,
        "job_name": workspace_id,
    }

    deploy_dir = deploy_dir if isinstance(deploy_dir, Path) else Path(deploy_dir)
    for job in schema_config.get("jobs", []):
        script_path = deploy_dir / job.get("path", "") / job.get("name", "")
        if script_path.exists():
            _run_schema_init_job(script_path, mapping, workspace_id, schema_name, state)

    organization_id = api_section["organization_id"]
    logger.info(f"  [dim]→ Creating workspace secret for [cyan]{workspace_id}[/cyan]...[/dim]")
    create_workspace_secret(
        namespace=env.environ_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        writer_password=api_config.get("writer-password", ""),
    )
    logger.info(f"  [dim]→ Creating CoAL ConfigMap for [cyan]{workspace_id}[/cyan]...[/dim]")
    create_coal_configmap(
        namespace=env.environ_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        db_host=db_host,
        db_port="5432",
        db_name=api_config.get("database-name", ""),
        schema_name=schema_name,
        writer_username=api_config.get("writer-username", ""),
    )


# ---------------------------------------------------------------------------
# Kubernetes PostgreSQL schema teardown (used by destroy)
# ---------------------------------------------------------------------------


def _handle_destroy_job_logs(k8s_job_name: str, schema_name: str, state: dict) -> None:
    """Fetch destroy-job logs and update state based on their content."""
    logs_process = subprocess.run(
        ["kubectl", "logs", f"job/{k8s_job_name}", "-n", env.environ_id],
        capture_output=True,
        text=True,
    )
    if logs_process.returncode != 0:
        logger.error(f"  [bold red]✘[/bold red] Failed to retrieve logs for job {k8s_job_name}")
        logger.debug(f"  [bold red]✘[/bold red] Logs retrieval output {logs_process.stdout} {logs_process.stderr}")
        return

    job_logs = logs_process.stdout or logs_process.stderr
    if "ERROR" in job_logs or "error" in job_logs:
        logger.error("  [bold red]✘[/bold red] Schema destruction failed inside the container")
        logger.debug(f"  [bold red]✘[/bold red] Job logs : {job_logs}")
    elif "does not exist" in job_logs:
        logger.info(f"  [yellow]⚠[/yellow] [dim]Schema [magenta]{schema_name}[/magenta] does not exist (nothing to clean)[/dim]")
        state["services"]["postgres"]["schema_name"] = ""
    else:
        logger.info(f"  [green]✔[/green] Schema destruction [magenta]{schema_name}[/magenta] completed successfully")
        state["services"]["postgres"]["schema_name"] = ""


def _wait_and_check_destroy_job(k8s_job_name: str, schema_name: str, state: dict) -> None:
    """Wait for the destroy job to complete, then inspect its logs."""
    logger.info(f"  [dim]→ Waiting for job [cyan]{k8s_job_name}[/cyan] to complete...[/dim]")
    wait_process = subprocess.run(
        ["kubectl", "wait", "--for=condition=complete", "job", k8s_job_name, f"--namespace={env.environ_id}", "--timeout=300s"],
        capture_output=True,
        text=True,
    )
    if wait_process.returncode != 0:
        logger.error(f"  [bold red]✘[/bold red] Job {k8s_job_name} did not complete successfully see babylon logs for details")
        logger.debug(f"  [bold red]✘[/bold red] Job wait output {wait_process.stdout} {wait_process.stderr}")
        return

    logger.info("  [dim]→ Checking job logs for errors...[/dim]")
    _handle_destroy_job_logs(k8s_job_name, schema_name, state)


def destroy_postgres_schema(schema_name: str, state: dict) -> None:
    """Destroy the PostgreSQL schema for a workspace.

    Applies a K8s destroy job rendered from the template at
    ``env.original_template_path / yaml / k8s_job_destroy.yaml``, waits for
    it to complete and clears the schema name from state on success.
    """
    if not schema_name:
        logger.warning("  [yellow]⚠[/yellow] [dim]No schema found ! skipping deletion[/dim]")
        return

    workspace_id_tmp = schema_name.replace("_", "-")
    db_host = get_postgres_service_host(env.environ_id)
    logger.info(f"  [dim]→ Destroying postgreSQL schema for workspace [bold cyan]{workspace_id_tmp}[/bold cyan]...[/dim]")

    pg_config = env.get_config_from_k8s_secret_by_tenant("postgresql-config", env.environ_id)
    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)

    if not pg_config or not api_config:
        logger.error("  [bold red]✘[/bold red] Failed to retrieve postgreSQL configuration from secrets")
        return

    mapping = {
        "namespace": env.environ_id,
        "db_host": db_host,
        "db_port": "5432",
        "cosmotech_api_database": api_config.get("database-name"),
        "cosmotech_api_admin_username": api_config.get("admin-username"),
        "cosmotech_api_admin_password": api_config.get("admin-password"),
        "cosmotech_api_writer_username": api_config.get("writer-username"),
        "cosmotech_api_reader_username": api_config.get("reader-username"),
        "workspace_schema": schema_name,
        "job_name": workspace_id_tmp,
    }
    destroy_jobs = env.original_template_path / "yaml" / "k8s_job_destroy.yaml"
    k8s_job_name = f"postgresql-destroy-{workspace_id_tmp}"
    kube_config.load_kube_config()
    k8s_client = client.ApiClient()

    with open(destroy_jobs, "r") as f:
        raw_content = f.read()

    yaml_dict = safe_load(Template(raw_content).safe_substitute(mapping))
    logger.info("  [dim]→ Applying kubernetes destroy job...[/dim]")
    try:
        utils.create_from_dict(k8s_client, yaml_dict, namespace=env.environ_id)
        _wait_and_check_destroy_job(k8s_job_name, schema_name, state)
    except Exception as e:
        logger.error("  [bold red]✘[/bold red] Unexpected error please check babylon logs file for details")
        logger.debug(f"  [bold red]✘[/bold red] {e}")


# ---------------------------------------------------------------------------
# Superset helpers
# Superset dashboard deployment (databases → datasets → charts → dashboards)
# ---------------------------------------------------------------------------

def _get_superset_csrf_token(base_url: str, bearer_token: str) -> str | None:
    """Fetches a CSRF token from Superset (required for import endpoints)."""
    url = f"{base_url.rstrip('/')}/api/v1/security/csrf_token/"
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {bearer_token}"},
            timeout=10,
        )
        response.raise_for_status()
        csrf = response.json().get("result")
        if not csrf:
            logger.error("  [bold red]✘[/bold red] CSRF token not found in Superset response")
        return csrf
    except Exception as exp:
        logger.error(f"  [bold red]✘[/bold red] Failed to fetch Superset CSRF token: {exp}")
        return None


def _get_existing_datasource(base_url: str, superset_jwt: str, display_name: str) -> dict | None:
    """Return the existing Superset database entry matching *display_name*, or None."""
    url = f"{base_url}/api/v1/database/"
    headers = {"Authorization": f"Bearer {superset_jwt}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        for db in response.json().get("result", []):
            if db.get("database_name") == display_name:
                return db
    except Exception as exp:
        logger.debug(f"  [dim] Could not list Superset databases: {exp}[/dim]")
    return None


def create_postgres_datasource(
    superset_config: dict,
    superset_jwt: str | None = None,
) -> dict | None:
    """
    Creates a new PostgreSQL database connection in Superset.
    """

    base_url = (superset_config.get("superset_url") or "").rstrip("/")
    if not base_url:
        logger.error("  [bold red]✘[/bold red] Superset base_url not found in superset_config")
        return None

    if superset_jwt:
        logger.debug("  [dim]→ Reusing existing Superset JWT for datasource creation[/dim]")
    else:
        superset_jwt = get_superset_token(base_url=base_url, config=superset_config)
        if not superset_jwt:
            logger.error("  [bold red]✘[/bold red] Could not obtain Superset JWT for datasource creation")
            return None

    # Superset CSRF token (Superset requires it for all write operations)
    csrf_token = _get_superset_csrf_token(base_url, superset_jwt)
    if not csrf_token:
        logger.error("  [bold red]✘[/bold red] Could not obtain Superset CSRF token for datasource creation")
        return None

    url = f"{base_url}/api/v1/database/"
    headers = {
        "Authorization": f"Bearer {superset_jwt}",
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token,
        "Referer": base_url,
    }

    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    db_name = api_config.get("database-name")

    display_name = env.environ_id

    # Check if the datasource already exists skip creation if so
    existing = _get_existing_datasource(base_url, superset_jwt, display_name)
    if existing:
        logger.warning(
            f"  [yellow]⚠[/yellow] Superset datasource '{display_name}' already exists "
            f"(id={existing.get('id')}) skipping creation!"
        )
        return existing

    sqlalchemy_uri = (
        f"postgresql+psycopg2://{api_config.get('writer-username')}:{api_config.get('writer-password')}"
        f"@{get_postgres_service_host(env.environ_id)}:5432/{db_name}"
    )
    payload = {
        "database_name": display_name,
        "sqlalchemy_uri": sqlalchemy_uri,
        "expose_in_sqllab": True,
        "allow_run_async": False,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        logger.info(f"  [bold green]✔[/bold green] Superset datasource '{display_name}' created successfully")
        return response.json()
    except Exception as exp:
        logger.error(f"  [bold red]✘[/bold red] Failed to create Superset datasource: {exp}")
        if hasattr(exp, "response") and exp.response is not None:
            logger.debug(f"  Response details: {exp.response.text}")
        return None

def _repack_zip(zip_path: Path, tmp_dir: Path) -> None:
    """Repack the contents of *tmp_dir* back into *zip_path*, replacing it in-place.
    """
    buf = BytesIO()
    with ZipFile(buf, "w", compression=8) as zf:  # 8 = ZIP_DEFLATED
        for file in sorted(tmp_dir.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(tmp_dir))
    zip_path.write_bytes(buf.getvalue())


def _patch_database_dir(tmp_dir: Path, sqlalchemy_uri: str, database_name: str) -> None:
    """Patch ``sqlalchemy_uri`` and ``database_name`` in every YAML file under tmp_dir/databases/."""

    db_dir = tmp_dir / "databases"
    if not db_dir.is_dir():
        logger.warning("  [yellow]⚠[/yellow] No 'databases/' folder found inside the ZIP skipping URI patch!")
        return

    # Matches:  sqlalchemy_uri: <anything to end of line>
    _uri_re = compile(r"^(sqlalchemy_uri:\s*).*$", MULTILINE)
    # Matches:  database_name: <anything to end of line>
    _name_re = compile(r"^(database_name:\s*).*$", MULTILINE)
    patched_files: list[str] = []
    for yaml_file in db_dir.glob("*.yaml"):
        try:
            raw = yaml_file.read_text(encoding="utf-8")
            result = raw
            if "sqlalchemy_uri" in result:
                result = _uri_re.sub(rf"\g<1>{sqlalchemy_uri}", result)
            if "database_name" in result:
                result = _name_re.sub(rf"\g<1>{database_name}", result)
            if result != raw:
                yaml_file.write_text(result, encoding="utf-8")
                patched_files.append(yaml_file.name)
                logger.debug(f"  [dim]→ Patched databases/{yaml_file.name}[/dim]")
        except Exception as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not patch {yaml_file.name}: {exc}")

    if patched_files:
        logger.info(
            f"  [bold green]✔[/bold green] Database YAML patched "
            f"database_name='{database_name}', 'sqlalchemy_uri' updated"
            f" in {len(patched_files)} file(s)"
        )
    else:
        logger.warning("  [yellow]⚠[/yellow] No database YAML files required patching")

def _patch_schema_in_datasets_dir(tmp_dir: Path, schema_name: str) -> None:
    """Patch the ``schema`` field in every dataset YAML under tmp_dir/datasets/.

    This function replaces the old schema value with the *schema_name* of the current workspace so the imported
    datasets point at the right schema in the target environment.
    """
    datasets_dir = tmp_dir / "datasets"
    if not datasets_dir.is_dir():
        logger.warning("  [yellow]⚠[/yellow] No 'datasets/' folder found inside the ZIP skipping schema patch")
        return

    # Matches:  schema: <old_value>
    # The value is a bare word (no quotes) Superset always writes it that way.
    _schema_re = compile(r"^(schema:\s*)(\S+)\s*$", MULTILINE)

    patched_files: list[str] = []
    for yaml_file in datasets_dir.rglob("*.yaml"):
        try:
            raw = yaml_file.read_text(encoding="utf-8")
            match = _schema_re.search(raw)
            if not match:
                continue
            old_schema = match.group(2)
            if old_schema == schema_name:
                continue  # already correct, skip
            patched = raw.replace(old_schema, schema_name)
            yaml_file.write_text(patched, encoding="utf-8")
            patched_files.append(yaml_file.name)
            logger.debug(f"  [dim]→ Patched schema in {yaml_file.name}: '{old_schema}' → '{schema_name}'[/dim]")
        except Exception as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not patch schema in {yaml_file.name}: {exc}")

    if patched_files:
        logger.info(
            f"  [bold green]✔[/bold green] Dataset schema patched "
            f"'{schema_name}' in {len(patched_files)} file(s)"
        )
    else:
        logger.info("  [yellow]⚠[/yellow] No datasets YAML files required schema patching")

# Matches the top-level ``uuid`` field in a Superset export YAML.
# Superset always writes it as:  uuid: <hex-uuid>  (no quotes, one per file)
_UUID_FIELD_RE = compile(
    r"^uuid:\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s*$",
    MULTILINE | IGNORECASE,
)


def _regenerate_superset_uuids(base_dir_path: str | Path) -> dict:
    """Regenerate all entity UUIDs in an unzipped Superset export directory.

    Superset exports form a strict dependency chain:
        Databases → Datasets (database_uuid) → Charts (dataset_uuid)
          → Dashboards (position[*].meta.uuid + native_filter_configuration targets)

    Strategy **pure text substitution, no YAML parse/dump**:
      Pass 1 : Scan every file's raw text for the top-level ``uuid:`` field.
               For each one found, generate a new uuid4() and record
               {old_uuid: new_uuid} in ``uuid_mapping``.
      Pass 2 : For every file, replace ALL occurrences of every old UUID
               with its corresponding new UUID using plain str.replace().
               Because UUIDs are 36-char hex strings that cannot appear
               accidentally in SQL or other content, this is safe and leaves
               every other byte of the file (multi-line SQL, escaped chars,
               indentation, comments) completely untouched.

    Args:
        base_dir_path: Path to the root of the unzipped Superset export
                       (the directory that contains charts/, dashboards/,
                       databases/, datasets/, metadata.yaml).

    Returns:
        The ``uuid_mapping`` dict {old_uuid: new_uuid} for logging.
    """
    base_dir = Path(base_dir_path)

    # Pass 1: Discover entity-owner UUIDs and build the mapping
    uuid_mapping: dict[str, str] = {}
    all_files: list[Path] = sorted(base_dir.rglob("*.yaml"))

    for yaml_file in all_files:
        raw = yaml_file.read_text(encoding="utf-8")
        match = _UUID_FIELD_RE.search(raw)
        if match:
            old_uuid = match.group(1).lower()
            uuid_mapping[old_uuid] = str(_uuid_mod.uuid4())

    if not uuid_mapping:
        logger.warning("  [yellow]⚠[/yellow] No UUIDs found in Superset export skipping regeneration")
        return {}

    # Pass 2: Replace every occurrence of every old UUID in every file
    for yaml_file in all_files:
        raw = yaml_file.read_text(encoding="utf-8")
        patched = raw
        for old_uuid, new_uuid in uuid_mapping.items():
            # Replace both lower-case and upper-case variants defensively
            patched = patched.replace(old_uuid, new_uuid)
            patched = patched.replace(old_uuid.upper(), new_uuid)
        if patched != raw:
            yaml_file.write_text(patched, encoding="utf-8")

    logger.info(
        f"  [dim]→ Regenerated and remapped {len(uuid_mapping)} UUIDs "
        f"across {len(all_files)} files in '{base_dir.name}'[/dim]"
    )
    return uuid_mapping

def deploy_superset_multiple_assets(
    superset_token: str,
    reports: list,
    state: dict,
    superset_config: dict,
    deploy_dir: Path,
    workspace_yaml_path: Path | None,
) -> bool:
    """Deploy Superset dashboard assets (patch-only, sequential per ZIP).

    This function performs the local preparation steps required before a
    Superset import. For each provided export ZIP it:

      1. Validates Superset base URL and fetches a CSRF token for write operations.
      2. Ensures a PostgreSQL datasource exists in Superset.
      3. Builds the target ``sqlalchemy_uri`` from Kubernetes secrets.
      4. Extracts the export ZIP to a temporary directory and normalises the content.
      5. Patches ``databases/*.yaml`` to set the correct
         ``sqlalchemy_uri`` and ``database_name`` so the exported database
         entry matches the datasource created in Superset.
      6. Patches all dataset YAML files to replace the source PostgreSQL
         schema name with the current workspace schema name.
      7. Regenerates all entity UUIDs in the export (databases, datasets,
         charts, dashboards) so each import uses a fresh set of UUIDs and
         avoids collisions on re-import or across environments.
      8. Re-packs the patched content back into the original ZIP file.
      9. Cleans up the temporary extraction directory.

    Important notes:
      - This function does NOT currently perform the HTTP "import" of the
        patched ZIP into Superset. It prepares and repacks the ZIP so an
        import step can be performed later (TODO: import wiring).
      - All file mutations use pure text substitution (no YAML parse/dump)
        to preserve multi-line SQL and original file formatting.

    Args:
        superset_token: Superset JWT obtained from Keycloak exchange.
        reports: List of dicts with 'name' and 'path' keys (paths are
            relative to ``deploy_dir`` when not absolute).
        state: Full Babylon state dict (used to derive the workspace_id →
            schema name).
        deploy_dir: Root deployment directory used to resolve report paths.
        workspace_yaml_path: Absolute path to the Workspace.yaml on disk
            (currently unused by this function but kept for future wiring).

    Returns:
        True if all reports were processed (extracted, patched, UUIDs
        regenerated and repacked) successfully; False if any ZIP was
        missing or an unrecoverable error occurred while preparing files.
    """
    base_url = superset_config.get("superset_url", "").rstrip("/")

    if not base_url:
        logger.error("  [bold red]✘[/bold red] Superset base_url not found in superset_config")
        return False

    logger.info(f"  [dim]→ Superset dashboard deployment for {len(reports)} zip file(s)...[/dim]")

    # CSRF token shared for the whole session
    csrf_token = _get_superset_csrf_token(base_url, superset_token)
    if not csrf_token:
        return False

    # PostgreSQL datasource created once with the already-exchanged Superset JWT
    datasource = create_postgres_datasource(
        superset_config=superset_config,
        superset_jwt=superset_token,
    )
    if datasource is None:
        logger.error("  [bold red]✘[/bold red] Aborting: datasource creation failed")
        return False
    # Build sqlalchemy_uri from K8s secrets
    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    if not api_config:
        logger.error("  [bold red]✘[/bold red] PostgreSQL API config secret not found")
        return False

    db_host = get_postgres_service_host(env.environ_id)
    sqlalchemy_uri = (
        f"postgresql+psycopg2://{api_config.get('writer-username')}:{api_config.get('writer-password')}"
        f"@{db_host}:5432/{api_config.get('database-name')}"
    )

    workspace_id = (state.get("services", {}).get("api", {}).get("workspace_id") or "")
    schema_name = workspace_id.replace("-", "_")

    all_ok = True
    abs_deploy_dir = Path(deploy_dir).resolve()
    for report in reports:
        name: str = report.get("name", "")
        rel_path: str = report.get("path", "")
        zip_path = (abs_deploy_dir / rel_path).resolve() if not Path(rel_path).is_absolute() else Path(rel_path).resolve()
        logger.info(f"  [dim]→ Preparing dashboard '{name}' for deployment...[/dim]")

        if not zip_path.exists():
            logger.error(f"  [bold red]✘[/bold red] ZIP not found {zip_path}")
            logger.debug(f"  [bold red]✘[/bold red] deploy_dir resolved to {abs_deploy_dir}")
            all_ok = False
            continue

        tmp_dir = Path(mkdtemp(prefix="babylon_superset_"))
        try:
            with ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_dir)

            top_level = [p for p in tmp_dir.iterdir() if p.is_dir()]
            content_dir = top_level[0] if len(top_level) == 1 else tmp_dir

            _patch_database_dir(content_dir, sqlalchemy_uri, database_name=env.environ_id)
            _patch_schema_in_datasets_dir(content_dir, schema_name)
            _regenerate_superset_uuids(content_dir)

            # Repack the patched content back into the original ZIP on disk
            _repack_zip(zip_path, tmp_dir)
            logger.info(f"  [bold green]✔[/bold green] Repacked patched ZIP [dim]{zip_path.name}[/dim]")

        finally:
            rmtree(tmp_dir, ignore_errors=True)

    return all_ok


def deploy_superset(
    reports: list,
    state: dict,
    superset_config: dict,
    deploy_dir: Path,
    workspace_yaml_path: Path | None,
) -> bool:
    """Authenticate with Superset (db provider) and deploy dashboard ZIPs sequentially."""

    base_url = superset_config.get("superset_url", "").rstrip("/")
    if not base_url:
        logger.error("  [bold red]✘[/bold red] Superset base_url not found in superset_config")
        return False

    valid_reports = [r for r in reports if isinstance(r, dict) and r.get("name") and r.get("path")]
    if not valid_reports:
        logger.warning("  [yellow]⚠[/yellow] Superset create is true but no valid reports found")
        return True

    superset_token = get_superset_token(base_url=base_url, config=superset_config)
    if not superset_token:
        logger.error("  [bold red]✘[/bold red] Failed to retrieve Superset token")
        return False

    return deploy_superset_multiple_assets(
        superset_token=superset_token,
        reports=valid_reports,
        superset_config=superset_config,
        state=state,
        deploy_dir=deploy_dir,
        workspace_yaml_path=workspace_yaml_path,
    )

def deploy_dashboard(
    provider: str,
    reports: list,
    state: dict,
    superset_config: dict,
    deploy_dir: Path,
    workspace_yaml_path: Path | None,
) -> bool:
    """Dispatch dashboard deployment to the correct provider handler."""
    if provider == "superset":
        return deploy_superset(reports, state, superset_config, deploy_dir, workspace_yaml_path)
    if provider == "powerbi":
        pass
        # return _deploy_powerbi(reports, state, workspace_yaml_path)
    logger.error(f"  [bold red]✘[/bold red] Unknown dashboard provider: '{provider}'")
    return False
