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
from re import MULTILINE, IGNORECASE, sub, compile, findall
from base64 import b64encode
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile

from logging import getLogger
from pathlib import Path
from string import Template
from textwrap import dedent
from typing import Callable
import uuid as _uuid_mod
from io import StringIO
from requests.exceptions import RequestException
import requests
from ruamel.yaml import YAML as _RYAML


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

# Matches the top-level ``uuid`` field in a Superset export YAML.
# Superset always writes it as:  uuid: <hex-uuid>  (no quotes, one per file)
_UUID_FIELD_RE = compile(
    r"^uuid:\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s*$",
    MULTILINE | IGNORECASE,
)

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
        logger.debug(f"  [dim]→ Could not list Superset databases: {exp}[/dim]")
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
            f"  [yellow]⚠[/yellow] [dim]Superset datasource '{display_name}' already exists "
            f"(id={existing.get('id')}) skipping creation![/dim]"
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

def _read_uuids_from_zip(zip_path: Path) -> set[str]:
    """Read all top-level entity UUIDs directly from YAML entries inside *zip_path*.

    Returns:
        A set of lowercase UUID strings found in the ZIP.
    """
    uuids: set[str] = set()
    try:
        with ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                if not member.endswith(".yaml"):
                    continue
                raw = zf.read(member).decode("utf-8", errors="replace")
                match = _UUID_FIELD_RE.search(raw)
                if match:
                    uuids.add(match.group(1).lower())
    except Exception as exc:
        logger.debug(f"  [dim]→ Could not read UUIDs from {zip_path.name}: {exc}[/dim]")
    return uuids


def _assets_exist_in_superset(base_url: str, superset_jwt: str, uuids: set[str]) -> dict[str, bool]:
    """Check which asset types from the export ZIP already exist in Superset.

    Queries datasets, charts, and dashboards endpoints independently and
    cross-references each result set against *uuids*`.

    The returned mapping is consumed by :func:`_regenerate_superset_uuids` so
    that UUIDs are only regenerated for components that are **not** yet deployed.

    Endpoints checked:
      - ``GET /api/v1/dataset/``   → key ``"datasets"``
      - ``GET /api/v1/chart/``     → key ``"charts"``
      - ``GET /api/v1/dashboard/`` → key ``"dashboards"``

    Returns:
        A dict ``{"datasets": bool, "charts": bool, "dashboards": bool}``
        where ``True`` means at least one UUID from the ZIP already exists
        in Superset for that component type.  On API failure the value
        defaults to ``False`` (safe path: regenerate UUIDs).
    """
    result: dict[str, bool] = {"datasets": False, "charts": False, "dashboards": False}
    if not uuids:
        return result

    headers = {"Authorization": f"Bearer {superset_jwt}"}

    # (folder_key, endpoint, uuid_field_in_response)
    _checks: list[tuple[str, str, str]] = [
        ("datasets",   "/api/v1/dataset/",   "uuid"),
        ("charts",     "/api/v1/chart/",     "uuid"),
        ("dashboards", "/api/v1/dashboard/", "uuid"),
    ]

    for folder_key, endpoint, uuid_field in _checks:
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                headers=headers,
                params={"page_size": 1000},
                timeout=10,
            )
            response.raise_for_status()
            existing = {
                (item.get(uuid_field) or "").lower()
                for item in response.json().get("result", [])
            }
            matched = uuids & existing
            if matched:
                result[folder_key] = True
                logger.debug(
                    f"  [dim]→ {folder_key}: {len(matched)} existing UUID(s) found "
                    f"UUIDs will NOT be regenerated for this component[/dim]"
                )
            else:
                logger.debug(f"  [dim]→ {folder_key}: no existing UUIDs will regenerate[/dim]")
        except Exception as exc:
            # Failure → treat as "not deployed" so UUID regen proceeds safely.
            logger.debug(f"  [dim]→ Could not query Superset {folder_key} endpoint: {exc}[/dim]")

    deployed = [k for k, v in result.items() if v]
    missing  = [k for k, v in result.items() if not v]
    if deployed:
        logger.info(f"  [yellow]⚠[/yellow] Already deployed in Superset {', '.join(deployed)}")
    if missing:
        logger.info(f"  [dim]→ Not yet deployed (will patch + regen UUIDs) {', '.join(missing)}[/dim]")

    return result


def _import_zip_to_superset(
    base_url: str,
    superset_jwt: str,
    csrf_token: str,
    zip_path: Path,
) -> bool:
    """POST a zip bundle to the Superset API to import all assets at once.

        Args:
            base_url:     Superset base URL (no trailing slash).
            superset_jwt: Valid Superset Bearer token.
            csrf_token:   CSRF token (refreshed immediately before this call).
            zip_path:     Path to the (patched) Superset export ZIP.

        Returns:
            True on successful import (HTTP 2xx), False on any error.
    """

    url = f"{base_url}/api/v1/assets/import/"
    headers = {
        "Authorization": f"Bearer {superset_jwt}",
        "X-CSRFToken": csrf_token,
        "Referer": base_url,
    }
    data  = {"overwrite": "true"}
    try:
        with zip_path.open("rb") as fh:
            files = {"bundle": (zip_path.name, fh, "application/zip")}
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)

        response.raise_for_status()
        logger.info(f"  [bold green]✔[/bold green] Zip imported '{zip_path.name}' into Superset successfully")
        return True
    
    except RequestException as exp:
        logger.error(f"  [bold red]✘[/bold red] Failed to import '{zip_path.name}' into Superset: {exp}")
        if exp.response is not None:
            try:
                logger.debug(f"  Response details: {exp.response.json()}")
            except ValueError:
                logger.debug(f"  Response details (raw): {exp.response.text[:2000]}")
            return False

    except Exception as exp:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error importing '{zip_path.name}': {exp}")
        return False


def update_variables_file_entry(
    variables_path: Path,
    key: str,
    uuid: str,
    original_id: str | None = None,
) -> bool:
    """Update a single dashboard entry in a Babylon variables YAML file in-place.

    Uses ``ruamel.yaml`` to preserve **all** existing formatting, comments, and
    template variables verbatim.  Only the target ``key`` block is touched no
    other keys, comments, or blank lines are affected.

    If ``key`` already exists as a mapping it updates only the ``uuid`` (and
    ``original_id`` when supplied).  If ``key`` is absent a new mapping block
    is appended at the end of the file.

    The function deliberately never writes to ``.tpl`` or template files; it
    accepts only the concrete variables YAML path.

    Args:
        variables_path: Absolute path to the Babylon ``variables.yaml`` file.
                        Must **not** be a template (``.tpl``) file.
        key:            Sanitised dashboard name used as the YAML key
                        (e.g. ``"expertview"``).
        uuid:           New embedded dashboard UUID to write.
        original_id:    Superset integer dashboard ID (as string).  When
                        ``None`` the field is left unchanged if already present,
                        or omitted from new entries.

    Returns:
        ``True`` on success, ``False`` on any error.
    """
    if not variables_path.is_file():
        logger.error(f"  [bold red]✘[/bold red] Variables file not found: {variables_path}")
        return False

    # Guard: refuse to touch template files
    if variables_path.suffix in {".tpl", ".tmpl", ".template"}:
        logger.error(f"  [bold red]✘[/bold red] Refusing to modify a template file: {variables_path}")
        return False

    try:
        ry = _RYAML()
        ry.preserve_quotes = True   # keep all quoted strings as-is
        ry.width = 4096             # prevent unexpected line-wrapping
        ry.best_map_flow_style = False

        raw = variables_path.read_text(encoding="utf-8")
        data = ry.load(raw)
        if data is None:
            data = ry.load("{}")  # empty file → start with an empty mapping

        entry = data.get(key)
        if isinstance(entry, dict):
            # Key already exists update only uuid (and original_id if given)
            entry["uuid"] = uuid
            if original_id is not None:
                entry["original_id"] = str(original_id)
        else:
            # Key absent or not a dict insert/overwrite with full block
            new_entry: dict = {"uuid": uuid}
            if original_id is not None:
                new_entry["original_id"] = str(original_id)
            data[key] = new_entry

        buf = StringIO()
        ry.dump(data, buf)
        variables_path.write_text(buf.getvalue(), encoding="utf-8")
        return True

    except OSError as exc:
        logger.error(f"  [bold red]✘[/bold red] File system error updating '{variables_path.name}': {exc}")
    except Exception as exc:
        logger.error(f"  [bold red]✘[/bold red] YAML error updating '{variables_path.name}': {exc}")
    return False


# ---------------------------------------------------------------------------
# Superset embedded-UUID fetch helpers  (extracted for SonarQube compliance)
# ---------------------------------------------------------------------------

def _get_filtered_dashboards(
    base_url: str,
    headers: dict,
    zip_uuids: set[str] | None,
) -> list[dict] | None:
    """Fetch all Superset dashboards and filter to those present in *zip_uuids*.

    Args:
        base_url:   Superset base URL (no trailing slash).
        headers:    Pre-built auth headers for the request.
        zip_uuids:  Set of dashboard UUIDs to keep.  ``None`` keeps all.

    Returns:
        Filtered list of dashboard dicts, or ``None`` on API error.
    """
    try:
        resp = requests.get(
            f"{base_url}/api/v1/dashboard/",
            headers=headers,
            params={"page_size": 1000},
            timeout=15,
        )
        resp.raise_for_status()
        all_dashboards: list[dict] = resp.json().get("result", [])
    except Exception as exc:
        logger.error(f"  [bold red]✘[/bold red] Could not list Superset dashboards: {exc}")
        return None

    if not zip_uuids:
        return all_dashboards

    filtered = [d for d in all_dashboards if (d.get("uuid") or "").lower() in zip_uuids]
    logger.debug(
        f"  [dim]→ Filtered to {len(filtered)}/{len(all_dashboards)} "
        "dashboards matching ZIP UUIDs[/dim]"
    )
    return filtered


def _enable_dashboard_embedding(
    base_url: str,
    superset_jwt: str,
    auth_headers: dict,
    integer_id: int,
    name: str,
) -> bool:
    """Enable embedding on a single Superset dashboard.

    Args:
        base_url:     Superset base URL.
        superset_jwt: Valid Superset Bearer token (used to refresh the CSRF token).
        auth_headers: Pre-built ``Authorization`` headers dict.
        integer_id:   Superset integer dashboard ID.
        name:         Human-readable dashboard name (used in log messages only).

    Returns:
        ``True`` if the POST succeeded (2xx), ``False`` otherwise.
    """
    csrf = _get_superset_csrf_token(base_url, superset_jwt)
    post_headers = {
        **auth_headers,
        "X-CSRFToken": csrf or "",
        "Referer": base_url,
        "Content-Type": "application/json",
    }
    enable_resp = requests.post(
        f"{base_url}/api/v1/dashboard/{integer_id}/embedded",
        headers=post_headers,
        json={"allowed_domains": []},
        timeout=10,
    )
    if not enable_resp.ok:
        logger.error(f"  [bold red]✘[/bold red] Could not enable embedding for '{name}' (id={integer_id}).")
        logger.debug(
            f"  [dim]→ Embedding failure details for '{name}' (id={integer_id}): "
            f"Status Code: {enable_resp.status_code}, Response: {enable_resp.text[:200]}[/dim]"
        )
        return False
    return True


def _get_embedded_uuid_for_dashboard(
    base_url: str,
    superset_jwt: str,
    auth_headers: dict,
    dashboard: dict,
) -> tuple[str, str, str] | None:
    """Enable embedding for one dashboard and return its embedded UUID details.

    Performs two calls:
    1. ``POST /api/v1/dashboard/{id}/embedded`` -> enables embedding (idempotent).
    2. ``GET  /api/v1/dashboard/{id}/embedded`` -> reads the embedded UUID back.

    Args:
        base_url:     Superset base URL.
        superset_jwt: Valid Superset Bearer token.
        auth_headers: Pre-built ``Authorization`` headers dict.
        dashboard:    A single dashboard dict from ``GET /api/v1/dashboard/``.

    Returns:
        A ``(key, embedded_uuid, original_id)`` tuple on success, or ``None``
        when the dashboard should be skipped (missing fields, embedding failed,
        or no UUID returned).
    """

    name: str = (dashboard.get("dashboard_title") or dashboard.get("slug") or "").strip()
    dash_uuid: str = (dashboard.get("uuid") or "").lower()
    integer_id: int | None = dashboard.get("id")

    if not dash_uuid or not name or not integer_id:
        logger.warning(f"  [yellow]⚠[/yellow] [dim]Skipping dashboard with missing name/uuid/id: {dashboard}[/dim]")
        return None

    key = sub(r"[^a-z0-9]", "", name.lower())
    if not key:
        logger.warning(f"  [yellow]⚠[/yellow] [dim]Dashboard '{name}' produced an empty key, skipping![/dim]")
        return None

    if not _enable_dashboard_embedding(base_url, superset_jwt, auth_headers, integer_id, name):
        return None

    try:
        emb_resp = requests.get(
            f"{base_url}/api/v1/dashboard/{integer_id}/embedded",
            headers=auth_headers,
            timeout=10,
        )
        emb_resp.raise_for_status()
    except Exception as exc:
        logger.error(f"  [bold red]✘[/bold red] Could not fetch embedded UUID for dashboard '{name}' (id={integer_id}).")
        logger.debug(
            f"  [dim]→ Fetch embedded UUID exception for '{name}' (id={integer_id}): {exc}[/dim]"
        )
        return None

    result_block: dict = emb_resp.json().get("result") or {}
    embedded_uuid: str = (result_block.get("uuid") or "").strip()

    if not embedded_uuid:
        logger.warning(
            f"  [yellow]⚠[/yellow] [dim]Dashboard '{name}' (id={integer_id}): "
            "no embedded UUID.[/dim]"
        )
        return None

    original_id = str(result_block.get("dashboard_id") or integer_id)
    logger.info(
        f"  [bold green]✔[/bold green] Embedding enabled for dashboard"
        f"'{name}' (key='{key}', uuid='{embedded_uuid}')"
    )
    return key, embedded_uuid, original_id


def _write_dashboard_updates_to_yaml(
    variables_yaml_path: Path,
    updates: dict[str, dict],
) -> bool:
    """Persist a ``{key: {uuid, original_id}}`` mapping into the variables YAML.

    Args:
        variables_yaml_path: Absolute path to the Babylon variables YAML file.
        updates:             Dict of ``{sanitised_key: {"uuid": ..., "original_id": ...}}``.

    Returns:
        ``True`` if at least one entry was written successfully, ``False`` otherwise.
    """
    if not variables_yaml_path.is_file():
        logger.error(f"  [bold red]✘[/bold red] Variables file not found: {variables_yaml_path}")
        return False

    any_written = False
    for key, entry in updates.items():
        ok = update_variables_file_entry(
            variables_path=variables_yaml_path,
            key=key,
            uuid=entry["uuid"],
            original_id=entry.get("original_id"),
        )
        if not ok:
            logger.warning(f"  [yellow]⚠[/yellow] [dim]Could not write '{key}' to '{variables_yaml_path.name}'[/dim]")
            continue
        any_written = True
        logger.debug(
            f"  [dim]→ Write success details for '{key}': "
            f"original_id={entry.get('original_id')}, "
            f"uuid={entry.get('uuid')}, "
            f"full_path='{variables_yaml_path}'[/dim]"
        )

    return any_written


def _fetch_and_store_embedded_dashboard_uuids(
    base_url: str,
    superset_jwt: str,
    zip_uuids: set[str] | None = None,
) -> bool:
    """Enable embedding and fetch the embedded UUID for dashboards imported from
    the ZIP, then persist them into the Babylon variables file.

    YAML structure written per dashboard::

        expertview:
          uuid: "abc-embedded-token-uuid"
          original_id: "42"

    Args:
        base_url:     Superset base URL.
        superset_jwt: Valid Superset Bearer token.
        zip_uuids:    Set of dashboard UUIDs read from the imported ZIP.
                      When provided, only dashboards matching this set are
                      processed.  Pass ``None`` to process all (not recommended).

    Returns:
        True if at least one embedded UUID was written; False on total failure.
    """
    if not env.variable_files:
        logger.warning(
            "  [yellow]⚠[/yellow] [dim]No variable files registered "
            "cannot store embedded dashboard UUIDs[/dim]"
        )
        return False

    variables_yaml_path = Path(env.variable_files[0])
    auth_headers = {"Authorization": f"Bearer {superset_jwt}"}

    # Step 1 Fetch and filter dashboards to only those from the ZIP
    dashboards = _get_filtered_dashboards(base_url, auth_headers, zip_uuids)
    if dashboards is None:
        return False
    if not dashboards:
        logger.warning("  [yellow]⚠[/yellow] [dim]No matching dashboards found in Superset skipping UUID feedback[/dim]")
        return False

    # Step 2 Enable embedding and collect the embedded UUID for each dashboard
    updates: dict[str, dict] = {}
    for dashboard in dashboards:
        result = _get_embedded_uuid_for_dashboard(base_url, superset_jwt, auth_headers, dashboard)
        if result is None:
            continue
        key, embedded_uuid, original_id = result
        updates[key] = {"uuid": embedded_uuid, "original_id": original_id}

    if not updates:
        logger.warning("  [yellow]⚠[/yellow] [dim]No embedded UUIDs retrieved, variables file not updated[/dim]")
        return False

    # Step 3 Persist the collected UUIDs into the variables YAML
    if not _write_dashboard_updates_to_yaml(variables_yaml_path, updates):
        return False

    logger.info(
        f"  [bold green]✔[/bold green] Variable file "
        f"[dim]'{variables_yaml_path.name}'[/dim] updated with "
        f"{len(updates)} embedded dashboard UUID(s)"
    )
    return True


def get_dashboard_embedded_uuid(yaml_data: dict, sanitised_key: str) -> str | None:
    """Safely retrieve the embedded UUID for a dashboard from loaded YAML data.

    The *yaml_data* dict is expected to contain entries written by
    :func:`_fetch_and_store_embedded_dashboard_uuids` in the shape::

        expertview:
          uuid: "abc-embedded-uuid"
          original_id: "42"

    A flat string value (legacy format ``expertview: "abc-uuid"``) is also
    accepted so old variables files don't break.

    Args:
        yaml_data:      Dict loaded from the Babylon variables YAML file.
        sanitised_key:  The sanitised dashboard name used as the YAML key
                        (e.g. ``"expertview"``).

    Returns:
        The embedded UUID string, or ``None`` if the key / uuid is absent.
    """
    if not yaml_data or not sanitised_key:
        return None

    entry = yaml_data.get(sanitised_key)
    if entry is None:
        logger.warning(
            f"  [yellow]⚠[/yellow] [dim]Dashboard key '{sanitised_key}' not found in variables "
            "UUID not available yet[/dim]"
        )
        return None

    # Flat legacy format: key → "uuid-string"
    if isinstance(entry, str):
        return entry or None

    # Current format: key → {uuid: ..., original_id: ...}
    if isinstance(entry, dict):
        uuid = entry.get("uuid")
        if not uuid:
            logger.warning(
                f"  [yellow]⚠[/yellow] [dim]Dashboard '{sanitised_key}' found in variables "
                "but 'uuid' field is empty[/dim]"
            )
        return uuid or None

    logger.warning(
        f"  [yellow]⚠[/yellow] [dim]Unexpected type for dashboard key '{sanitised_key}' "
        f"in variables: {type(entry).__name__}[/dim]"
    )
    return None

def _patch_metadata(content_dir: Path) -> None:
    """Ensure metadata.yaml declares ``type: assets`` for the assets import endpoint.

    Superset's ``/api/v1/assets/import/`` endpoint calls
    ``validate_metadata_type(metadata, "assets", ...)`` and rejects ZIPs whose
    ``metadata.yaml`` has any other type (e.g. ``type: Dashboard``).  This
    function rewrites the ``type:`` field in-place using pure regex so YAML
    formatting is preserved.
    """
    meta_file = content_dir / "metadata.yaml"

    if not meta_file.is_file():
        logger.warning("  [yellow]⚠[/yellow] [dim]metadata.yaml not found — skipping type patch![/dim]")
        return

    try:
        raw = meta_file.read_text(encoding="utf-8")
        
        # Matches 'type: ' followed by anything until the end of the line.
        # This safely catches multi-word or quoted types like 'type: "Dashboard"'.
        patched = sub(
            pattern=r"^(type:\s*).*$", 
            repl=r"\g<1>assets", 
            string=raw, 
            flags=MULTILINE
        )
        
        if patched != raw:
            meta_file.write_text(patched, encoding="utf-8")
            logger.debug("  [dim]→ Patched 'metadata.yaml' type 'assets'[/dim]")
        
    except OSError as exp:
        logger.error(f"  [bold red]✘[/bold red] File system error while patching 'metadata.yaml': {exp}")

def _repack_zip(zip_path: Path, tmp_dir: Path) -> None:
    """Repack the contents of *tmp_dir* back into *zip_path*, replacing it in-place.

    The ZIP therefore MUST have exactly one root folder, and after stripping
    the entries must be ``charts/X.yaml``, ``datasets/Y.yaml``,
    ``metadata.yaml``, etc.
    """
    root_name = zip_path.stem

    # If there is exactly one item in the extracted contents and it's a directory,
    # use it as the base so we don't double-nest. Otherwise, treat tmp_dir as the base.
    tmp_items = list(tmp_dir.iterdir())
    if len(tmp_items) == 1 and tmp_items[0].is_dir():
        base = tmp_items[0]
    else:
        base = tmp_dir

    try:
        # Write directly to disk instead of buffering the whole ZIP in memory
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
            for file in sorted(base.rglob("*")):
                if file.is_file():
                    # .as_posix() ensures forward slashes in the ZIP, even on Windows
                    arcname = f"{root_name}/{file.relative_to(base).as_posix()}"
                    zf.write(file, arcname)
                    
        logger.info(f"  [bold green]✔[/bold green] Successfully repacked a ZIP [dim]{zip_path.name}[/dim]")
        
    except OSError as exp:
        logger.error(f"  [bold red]✘[/bold red] File system error while repacking '{zip_path.name}': {exp}")
        raise


def _patch_database_dir(tmp_dir: Path, sqlalchemy_uri: str, database_name: str, db_uuid: str = "") -> None:
    """Patch connection fields and pin the UUID in every YAML under tmp_dir/databases/.

    Fields updated per file:
    - ``sqlalchemy_uri:`` — replaced with the current environment URI.
    - ``database_name:``  — replaced with *database_name* (``env.environ_id``).
    - ``uuid:``           — replaced with *db_uuid* when provided, so the
      imported record matches the Superset-assigned UUID of the already-created
      database connection and no duplicate is created on import.

    Args:
        tmp_dir:        Root of the unzipped export.
        sqlalchemy_uri: Full SQLAlchemy connection string for the target env.
        database_name:  Superset display name for the database (``env.environ_id``).
        db_uuid:        UUID returned by the Superset database API after
                        creation/lookup.  Pass an empty string to skip UUID pinning.
    """
    db_dir = tmp_dir / "databases"
    if not db_dir.is_dir():
        logger.warning("  [yellow]⚠[/yellow] No 'databases/' folder found inside the ZIP skipping database patch!")
        return

    _uri_re  = compile(r"^(sqlalchemy_uri:\s*).*$",              MULTILINE)
    _name_re = compile(r"^(database_name:\s*).*$",               MULTILINE)
    _uuid_re = compile(r"^(uuid:\s*)([0-9a-f-]{36})\s*$",        MULTILINE | IGNORECASE)

    patched_files: list[str] = []
    for yaml_file in db_dir.glob("*.yaml"):
        try:
            raw = yaml_file.read_text(encoding="utf-8")
            result = raw

            if "sqlalchemy_uri" in result:
                result = _uri_re.sub(lambda m: f"{m.group(1)}{sqlalchemy_uri}", result)
                
            if "database_name" in result:
                result = _name_re.sub(lambda m: f"{m.group(1)}{database_name}", result)
                
            if db_uuid and "uuid" in result:
                result = _uuid_re.sub(lambda m: f"{m.group(1)}{db_uuid}", result)

            if result != raw:
                yaml_file.write_text(result, encoding="utf-8")
                patched_files.append(yaml_file.name)
                logger.debug(f"  [dim]→ Patched databases/{yaml_file.name}[/dim]")

        except Exception as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not patch {yaml_file.name}: {exc}")

    if patched_files:
        uuid_note = f", uuid='{db_uuid}'" if db_uuid else ""
        logger.info(
            f"  [bold green]✔[/bold green] Database YAML patched "
            f"(database_name='{database_name}', sqlalchemy_uri updated{uuid_note}) "
            f"in {len(patched_files)} file(s)"
        )
    else:
        logger.warning("  [yellow]⚠[/yellow] [dim]No database YAML files required patching![/dim]")

def _patch_schema_in_datasets_dir(tmp_dir: Path, schema_name: str, db_uuid: str = "") -> None:
    """Patch schema references and pin the database UUID in every dataset YAML.

    Two passes over ``tmp_dir/datasets/**/*.yaml``:

    1. **Schema patch** finds the first ``schema: <value>`` line in the file,
       treats that value as the source schema name, and replaces *every*
       occurrence of it in the file (covers both the ``schema:`` field and any
       inline SQL that references ``old_schema.table_name``).

    2. **database_uuid patch** when *db_uuid* is supplied, replaces the
       ``database_uuid: <any-uuid>`` field with the real Superset-assigned UUID
       so every dataset correctly references the already-created DB connection.

    Args:
        tmp_dir:     Root of the unzipped export.
        schema_name: Target PostgreSQL schema for the current workspace.
        db_uuid:     Superset database UUID.  Pass an empty string to skip the
                     ``database_uuid:`` pin (e.g. when the UUID is not yet known).
    """
    datasets_dir = tmp_dir / "datasets"
    if not datasets_dir.is_dir():
        logger.warning("  [yellow]⚠[/yellow] No 'datasets/' folder found inside the ZIP skipping dataset patch!")
        return

    _schema_re      = compile(r"^(schema:\s*)(\S+)\s*$",                     MULTILINE)
    _db_uuid_re     = compile(r"^(database_uuid:\s*)([0-9a-f-]{36})\s*$",    MULTILINE | IGNORECASE)

    schema_patched: list[str] = []
    db_uuid_patched: int      = 0

    for yaml_file in datasets_dir.rglob("*.yaml"):
        try:
            raw = yaml_file.read_text(encoding="utf-8")
            result = raw

            # --- Schema replacement (field + all SQL occurrences) ----------
            match = _schema_re.search(result)
            if match:
                old_schema = match.group(2)
                if old_schema != schema_name:
                    result = result.replace(old_schema, schema_name)
                    schema_patched.append(yaml_file.name)
                    logger.debug(
                        f"  [dim]→ Patched schema in {yaml_file.name}: "
                        f"'{old_schema}' → '{schema_name}'[/dim]"
                    )

            # --- database_uuid replacement ---------------------------------
            if db_uuid and "database_uuid" in result:
                new_result = _db_uuid_re.sub(rf"\g<1>{db_uuid}", result)
                if new_result != result:
                    db_uuid_patched += 1
                    logger.debug(
                        f"  [dim]→ Patched 'database_uuid' in {yaml_file.name} → {db_uuid}[/dim]"
                    )
                    result = new_result

            if result != raw:
                yaml_file.write_text(result, encoding="utf-8")

        except Exception as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not patch dataset {yaml_file.name}: {exc}")

    if schema_patched:
        logger.info(
            f"  [bold green]✔[/bold green] Dataset schema patched "
            f"'{schema_name}' in {len(schema_patched)} file(s)"
        )
    else:
        logger.info("  [yellow]⚠[/yellow] [dim]No dataset YAML files required schema patching![/dim]")

    if db_uuid_patched:
        logger.info(
            f"  [bold green]✔[/bold green] Dataset 'database_uuid' patched "
            f"'{db_uuid}' in {db_uuid_patched} file(s)"
        )
    elif db_uuid:
        logger.debug("  [dim]→ No dataset files had a 'database_uuid' field to pin[/dim]")

def _regenerate_superset_uuids(base_dir_path: str | Path, existing: dict[str, bool] | None = None) -> dict:
    """Regenerate UUIDs for Superset components that haven't been deployed yet.

    Skips the 'databases' folder and any folders marked as deployed in the `existing` map. 
    Generates new UUIDs for the remaining active components, then updates all YAML files 
    so that cross-references (e.g., a chart pointing to a dataset) remain unbroken.

    Args:
        base_dir_path: Root directory of the unzipped Superset export.
        existing: Optional map of {folder_name: is_deployed} (e.g., {"charts": True}).

    Returns:
        A dictionary mapping {old_uuid: new_uuid}. Returns empty if none were regenerated.
    """
    base_dir = Path(base_dir_path)
    existing = existing or {}

    # "databases" is always skipped; others are skipped if marked True in `existing`
    skip_folders = {"databases"} | {folder for folder, deployed in existing.items() if deployed}
    # "themes" is optional present in some ZIPs, absent in others always regenerate when found
    active = sorted({"datasets", "charts", "dashboards", "themes"} - skip_folders)

    logger.debug(f"  [dim]→ UUID regen active: {active or 'none'}, skipped: {sorted(skip_folders)}[/dim]")

    all_files: list[Path] = sorted(base_dir.rglob("*.yaml"))
    uuid_mapping: dict[str, str] = {}

    for yaml_file in all_files:
        try:
            top_folder = yaml_file.relative_to(base_dir).parts[0]
        except (ValueError, IndexError):
            top_folder = ""

        if top_folder in skip_folders:
            continue  # preserve existing UUID for this component
        try:
            raw = yaml_file.read_text(encoding="utf-8")
            match = _UUID_FIELD_RE.search(raw)
            if match:
                # Group 1 is the only capture group: the 36-character UUID string
                old_uuid = match.group(1).lower()
                uuid_mapping[old_uuid] = str(_uuid_mod.uuid4())
        except (OSError, UnicodeError) as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not read {yaml_file.name} for UUID extraction: {exc}")

    if not uuid_mapping:
        logger.info("  [dim]→ No UUIDs required regeneration (all components already deployed)[/dim]")
        return {}
    
    # Pass 2 Replace every collected UUID across ALL files so that
    # cross-references (e.g. chart → dataset_uuid) stay consistent.
    for yaml_file in all_files:
        try:
            raw = yaml_file.read_text(encoding="utf-8")
            patched = raw
            
            for old_uuid, new_uuid in uuid_mapping.items():
                patched = patched.replace(old_uuid, new_uuid)
                patched = patched.replace(old_uuid.upper(), new_uuid)
                
            if patched != raw:
                yaml_file.write_text(patched, encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not update UUIDs in {yaml_file.name}: {exc}")

    logger.info(
        f"  [bold green]✔[/bold green] Regenerated {len(uuid_mapping)} UUID(s) "
        f"for {', '.join(active) or 'none'} "
        f"across {len(all_files)} file(s)"
    )
    return uuid_mapping


def _setup_database_and_csrf(
    base_url: str, 
    superset_token: str, 
    superset_config: dict
) -> tuple[str | None, str | None, str | None]:
    """Handles pre-flight checks: CSRF, Datasource creation, and DB URI building."""
    
    csrf_token = _get_superset_csrf_token(base_url, superset_token)
    if not csrf_token:
        logger.error("  [bold red]✘[/bold red] Could not obtain CSRF token.")
        return None, None, None

    datasource = create_postgres_datasource(
        superset_config=superset_config,
        superset_jwt=superset_token,
    )
    
    if datasource is None:
        logger.error("  [bold red]✘[/bold red] Aborting: datasource creation failed.")
        return None, None, None

    _ds_body = datasource.get("result") or datasource
    db_uuid: str = (_ds_body.get("uuid") or "").lower()

    if db_uuid:
        logger.debug(f"  [dim]→ Superset database UUID resolved: {db_uuid}[/dim]")
    else:
        logger.warning(f"  [yellow]⚠[/yellow] [dim]Could not extract UUID from datasource response.[/dim]")
        logger.debug(f"  [dim]→ Database UUID will not be pinned. Raw datasource: {_ds_body}[/dim]")

    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    if not api_config:
        logger.error("  [bold red]✘[/bold red] PostgreSQL API config secret not found.")
        return None, None, None

    db_host = get_postgres_service_host(env.environ_id)
    sqlalchemy_uri = (
        f"postgresql+psycopg2://{api_config.get('writer-username')}:{api_config.get('writer-password')}"
        f"@{db_host}:5432/{api_config.get('database-name')}"
    )
    
    return csrf_token, db_uuid, sqlalchemy_uri


def _process_dashboard_zip(
    report: dict,
    abs_deploy_dir: Path,
    base_url: str,
    superset_token: str,
    csrf_token: str,
    sqlalchemy_uri: str,
    db_uuid: str,
    schema_name: str,
) -> tuple[bool, set[str]]:
    """Handles the extraction, patching, repacking, and importing of a single ZIP."""
    
    name: str = report.get("name", "")
    rel_path: str = report.get("path", "")
    
    path_obj = Path(rel_path)
    zip_path = path_obj.resolve() if path_obj.is_absolute() else (abs_deploy_dir / rel_path).resolve()
    
    logger.info(f"  [dim]→ Preparing dashboard '{name}' for deployment...[/dim]")

    if not zip_path.exists():
        logger.error(f"  [bold red]✘[/bold red] ZIP not found: {zip_path.name}")
        logger.debug(f"  [dim]→ Deploy dir resolved to {abs_deploy_dir}. Missing file: {zip_path}[/dim]")
        return False, set()

    zip_uuids = _read_uuids_from_zip(zip_path)
    existing_map = _assets_exist_in_superset(base_url, superset_token, zip_uuids)
    new_dashboard_uuids: set[str] = set()

    try:
        with TemporaryDirectory(prefix="babylon_superset_") as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)

            with ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_dir)

            tmp_items = list(tmp_dir.iterdir())
            content_dir = tmp_items[0] if len(tmp_items) == 1 and tmp_items[0].is_dir() else tmp_dir

            _regenerate_superset_uuids(content_dir, existing_map)
            _patch_metadata(content_dir)
            _patch_database_dir(content_dir, sqlalchemy_uri, database_name=env.environ_id, db_uuid=db_uuid)
            _patch_schema_in_datasets_dir(content_dir, schema_name, db_uuid=db_uuid)

            dashboards_dir = content_dir / "dashboards"
            if dashboards_dir.is_dir():
                for df in dashboards_dir.rglob("*.yaml"):
                    try:
                        raw = df.read_text(encoding="utf-8")
                        m = _UUID_FIELD_RE.search(raw)
                        if m:
                            new_dashboard_uuids.add(m.group(1).lower())
                    except OSError as e:
                        logger.warning(f"  [yellow]⚠[/yellow] [dim]Could not read YAML file '{df.name}': {e}[/dim]")

            _repack_zip(zip_path, tmp_dir)

    except (OSError, BadZipFile) as exc:
        logger.error(f"  [bold red]✘[/bold red] File system or ZIP error while processing '{zip_path.name}'.")
        logger.debug(f"  [dim]→ Exception details for '{zip_path.name}': {exc}[/dim]")
        return False, set()

    if not _import_zip_to_superset(base_url, superset_token, csrf_token, zip_path):
        logger.error(f"  [bold red]✘[/bold red] Failed to import ZIP '{zip_path.name}' to Superset.")
        return False, set()

    return True, new_dashboard_uuids


def _build_dashboard_ext_args(fallback_empty: bool = False, template_content: str = "") -> dict:
    """Extract embedded dashboard UUIDs from the Babylon variables file.

        Args:
            fallback_empty:   If True, missing UUIDs and unresolved template variables 
                            are mapped to empty strings (safe phase-1 render).
            template_content: Raw Workspace template string, used to discover missing
                            variables when fallback_empty is True.

        Returns:
            A dictionary mapping template keys to UUID strings (or empty strings).
    """
    if not env.variable_files:
        return {}
    try:
        raw = Path(env.variable_files[0]).read_text(encoding="utf-8")
        variables: dict = safe_load(raw) or {}
    except OSError:
        return {}

    ext: dict = {}

    # Only treat entries that carry both "uuid" and "original_id" as dashboard
    # records.  This prevents misidentifying other dict-valued keys (e.g. the
    # "security:" ACL block) as dashboard entries.
    for key, value in variables.items():
        if not isinstance(value, dict):
            continue
        if "uuid" not in value or "original_id" not in value:
            continue  # not a dashboard entry skip
        uuid = get_dashboard_embedded_uuid(variables, key)
        if uuid:
            ext[key] = uuid
        elif fallback_empty:
            ext[key] = ""

    # When rendering phase-1 (fallback_empty=True), also pre-populate every
    # variable reference found in the template that is not already resolved by
    # the variables file or ext dict.
    # NOTE: file_content arrives pre-escaped ({{ → ${ , }} → }) from apply.py,
    # so we scan for Mako-style ${varname} syntax, not {{varname}}.
    if fallback_empty and template_content:
        known = variables.keys() | ext.keys()
        for var in findall(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}", template_content):
            if var not in known:
                ext[var] = ""

    return ext

def deploy_superset_multiple_assets(
    superset_token: str,
    reports: list,
    state: dict,
    superset_config: dict,
    deploy_dir: Path,
) -> tuple[bool, set[str]]:
    """Deploy Superset dashboard assets.

    Pre-flight (once per call):
    - Validates superset_url and obtains a CSRF token.
    - Idempotently creates the PostgreSQL datasource.
    - Builds the sqlalchemy_uri and schema_name from state/secrets.

    Per-ZIP processing:
    1. Queries Superset to find which component types are already deployed.
    2. Extracts the ZIP to a temporary directory.
    3. Regenerates UUIDs (skipping components already in Superset).
    4. Patches metadata and connection fields (schema, URI, db UUID).
    5. Repacks the patched content and imports it via the Superset API.

    Args:
        superset_token:      Superset JWT obtained from Keycloak exchange.
        reports:             List of dicts with 'name' and 'path' keys.
        state:               Full Babylon state dict.
        superset_config:     Dict with at least 'superset_url'.
        deploy_dir:          Root deployment directory used to resolve report paths.

    Returns:
        A tuple: (True if every report imported successfully, Set of all processed dashboard UUIDs)
    """
    base_url = superset_config.get("superset_url", "").rstrip("/")

    if not base_url:
        logger.error("  [bold red]✘[/bold red] Superset base_url not found in configuration.")
        logger.debug(f"  [dim]→ Provided superset_config: {superset_config}[/dim]")
        return False, set()

    logger.info(f"  [dim]→ Superset dashboard deployment for {len(reports)} zip file(s)...[/dim]")

    # 1. Pre-flight Setup
    csrf_token, db_uuid, sqlalchemy_uri = _setup_database_and_csrf(
        base_url, superset_token, superset_config
    )
    if not csrf_token or not sqlalchemy_uri:
        return False, set()

    workspace_id = (state.get("services", {}).get("api", {}).get("workspace_id") or "")
    schema_name = workspace_id.replace("-", "_")

    # 2. Process all ZIPs
    all_ok = True
    all_zip_uuids: set[str] = set()
    abs_deploy_dir = Path(deploy_dir).resolve()

    for report in reports:
        success, new_uuids = _process_dashboard_zip(
            report=report,
            abs_deploy_dir=abs_deploy_dir,
            base_url=base_url,
            superset_token=superset_token,
            csrf_token=csrf_token,
            sqlalchemy_uri=sqlalchemy_uri,
            db_uuid=db_uuid or "",
            schema_name=schema_name,
        )
        
        if not success:
            all_ok = False
            
        all_zip_uuids |= new_uuids

    return all_ok, all_zip_uuids


def deploy_superset(
    reports: list,
    state: dict,
    superset_config: dict,
    deploy_dir: Path,
) -> tuple[bool, set[str]]:
    """Authenticate with Superset (db provider) and deploy dashboard ZIPs sequentially.

    Returns:
        A tuple ``(success, zip_uuids)`` where *zip_uuids* is the union of all
        dashboard UUIDs read from every processed ZIP used by the caller to
        filter the embedded-UUID fetch to only the imported dashboards.
    """
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
        deploy_dir=deploy_dir
    )

def deploy_dashboard(
    provider: str,
    reports: list,
    state: dict,
    superset_config: dict,
    deploy_dir: Path,
) -> tuple[bool, set[str]]:
    """Dispatch dashboard deployment to the correct provider handler.

    Returns:
        A tuple ``(success, zip_uuids)``.  *zip_uuids* is only populated for
        the ``"superset"`` provider and contains the union of all dashboard
        UUIDs from the processed ZIPs.
    """
    if provider == "superset":
        return deploy_superset(reports, state, superset_config, deploy_dir)
    if provider == "powerbi":
        pass
        # return _deploy_powerbi(reports, state, workspace_yaml_path)
    logger.error(f"  [bold red]✘[/bold red] Unknown dashboard provider: '{provider}'")
    return False
