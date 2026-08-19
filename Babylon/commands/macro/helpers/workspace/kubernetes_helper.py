"""
Kubernetes helpers for workspace deployment and teardown.
"""

import subprocess
from base64 import b64encode
from logging import getLogger
from pathlib import Path
from string import Template
from textwrap import dedent

from kubernetes import client, utils
from kubernetes.utils import FailToCreateError
from yaml import safe_load

from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()

# Schema deployment public entry point

def deploy_postgres_schema(
    workspace_id: str,
    schema_config: dict,
    api_section: dict,
    deploy_dir: Path,
    state: dict,
    provider: str = "superset",
) -> None:
    """Initialize the PostgreSQL schema and workspace resources.

    The provider determines how database and user names are resolved:
    Superset uses the configured PostgreSQL Secret values, while Power BI
    derives names from the tenant. Passwords always come from the Secret.
    """
    db_host = get_postgres_host(env.environ_id, provider)
    logger.info(f"  [dim]→ Initializing PostgreSQL schema for workspace [bold cyan]{workspace_id}[/bold cyan]...[/dim]")

    # pg_config = env.get_config_from_k8s_secret_by_tenant("postgresql-config", env.environ_id)
    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    # if not pg_config or not api_config:
    #     return
    if not api_config:
        return

    identities = _resolve_postgres_identities(env.environ_id, provider, api_config)

    schema_name = workspace_id.replace("-", "_")
    mapping = {
        "namespace": env.environ_id,
        "db_host": db_host,
        "db_port": "5432",
        "cosmotech_api_database": identities["database_name"],
        "cosmotech_api_admin_username": identities["admin_username"],
        "cosmotech_api_admin_password": api_config.get("admin-password", ""),
        "cosmotech_api_writer_username": identities["writer_username"],
        "cosmotech_api_reader_username": identities["reader_username"],
        "workspace_schema": schema_name,
        "job_name": workspace_id,
    }

    deploy_dir = deploy_dir if isinstance(deploy_dir, Path) else Path(deploy_dir)

    for job in schema_config.get("jobs", []):
        script_path = deploy_dir / job.get("path", "") / job.get("name", "")
        if script_path.exists():
            _run_schema_init_job(script_path, mapping, workspace_id, schema_name, state)

    organization_id = api_section["organization_id"]

    logger.info(f"  [dim]→ Creating workspace Secret for [cyan]{workspace_id}[/cyan]...[/dim]")
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
        db_name=identities["database_name"],
        schema_name=schema_name,
        writer_username=identities["writer_username"],
    )

# PostgreSQL identity resolution (Internal vs External mode)

_SUPPORTED_POSTGRES_PROVIDERS = {"superset", "powerbi"}

def _resolve_postgres_identities(tenant: str, provider: str, api_config: dict) -> dict[str, str]:
    """Resolve PostgreSQL database and user identities for the provider.

    Power BI uses names derived from the tenant for external PostgreSQL.
    Superset uses the identities configured in the PostgreSQL Secret.
    Unsupported providers fall back to the Superset configuration.
    """
    provider_key = (provider or "").strip().lower()

    if provider_key not in _SUPPORTED_POSTGRES_PROVIDERS:
        logger.warning(
            f"  [yellow]⚠[/yellow] Unknown PostgreSQL provider '{provider}' "
            "falling back to Internal Postgres (superset) identity resolution"
        )
        provider_key = "superset"

    if provider_key == "powerbi":
        clean_prefix = tenant.replace("-", "_")
        return {
            "database_name": f"{tenant}",
            "admin_username": f"{clean_prefix}_cosmotech_api_admin",
            "writer_username": f"{clean_prefix}_cosmotech_api_writer",
            "reader_username": f"{clean_prefix}_cosmotech_api_reader",
        }

    return {
        "database_name": api_config.get("database-name", ""),
        "admin_username": api_config.get("admin-username", ""),
        "writer_username": api_config.get("writer-username", ""),
        "reader_username": api_config.get("reader-username", ""),
    }

# PostgreSQL host resolution (Internal vs External mode)

def get_postgres_host(namespace: str, provider: str = "superset") -> str:
    """Resolve the PostgreSQL host for the selected provider.

    Power BI uses the external Azure PostgreSQL host; all other providers
    use the in-cluster PostgreSQL service.
    """
    provider_key = (provider or "").strip().lower()

    if provider_key == "powerbi":
        return get_external_postgres_host()

    return get_postgres_service_host(namespace)

def get_external_postgres_host() -> str:
    """Resolve the external Azure PostgreSQL host.
    """
    variables = env.get_variables()
    explicit_host = variables.get("external_postgres_host")
    if explicit_host:
        return explicit_host

    cluster_name = variables.get("cluster_name", "")
    if not cluster_name:
        logger.warning(
            "  [yellow]⚠[/yellow] 'cluster_name' is not set in variables.yaml "
            "external PostgreSQL FQDN may be incorrect"
        )
    return f"csm-{cluster_name}.postgres.database.azure.com"

# PostgreSQL service discovery (Internal / in-cluster)

def get_postgres_service_host(namespace: str) -> str:
    """Discover the PostgreSQL service name in a namespace to build its FQDN.
    """
    try:
        k8s_client = env.get_kubernetes_client()
        services = k8s_client.list_namespaced_service(namespace)

        for svc in services.items:
            labels = svc.metadata.labels or {}
            if "postgresql" in svc.metadata.name or labels.get("app.kubernetes.io/name") == "postgresql":
                logger.debug(f"  [dim]→ Found PostgreSQL service {svc.metadata.name}[/dim]")
                return f"{svc.metadata.name}.{namespace}.svc.cluster.local"

        return f"postgresql.{namespace}.svc.cluster.local"
    except Exception as e:
        logger.warning("  [yellow]⚠[/yellow] PostgreSQL service discovery failed falling back to default hostname")
        logger.debug(f"  Exception details: {e}", exc_info=True)
        return f"postgresql.{namespace}.svc.cluster.local"

# K8s Secret and ConfigMap create

def create_workspace_secret(
    namespace: str,
    organization_id: str,
    workspace_id: str,
    writer_password: str,
) -> bool:
    """Create a Kubernetes Secret for a workspace containing API and PostgreSQL credentials.

    The secret is named ``<organization_id>-<workspace_id>`` and holds all
    environment variables required by workspace.
    """
    secret_name = f"{organization_id}-{workspace_id}"
    encoded_data = {
        "POSTGRES_USER_PASSWORD": b64encode(writer_password.encode("utf-8")).decode("utf-8"),
    }

    secret = client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(name=secret_name, namespace=namespace),
        type="Opaque",
        data=encoded_data,
    )

    try:
        k8s_client = env.get_kubernetes_client()
        k8s_client.create_namespaced_secret(namespace=namespace, body=secret)
        logger.info(f"  [bold green]✔[/bold green] Secret [magenta]{secret_name}[/magenta] created")
        return True
    except client.ApiException as e:
        if getattr(e, "status", None) == 409:
            logger.warning(
                f"  [yellow]⚠[/yellow] [dim]Secret [magenta]{secret_name}[/magenta] is already configured skipping creation[/dim]"
            )
            return True
        logger.error(f"  [bold red]✘[/bold red] Failed to create secret {secret_name}: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error creating Secret '{secret_name}'")
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
    contains a ``coal-config.toml`` key with Postgres output configuration.
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
        k8s_client = env.get_kubernetes_client()
        k8s_client.create_namespaced_config_map(namespace=namespace, body=configmap)
        logger.info(f"  [bold green]✔[/bold green] ConfigMap [magenta]{configmap_name}[/magenta] created")
        return True
    except client.ApiException as e:
        if e.status == 409:
            logger.warning(
                f"  [yellow]⚠[/yellow] [dim]ConfigMap [magenta]{configmap_name}[/magenta] is already "
                f"configured skipping creation[/dim]"
            )
            return True
        logger.error(f"  [bold red]✘[/bold red] Failed to create ConfigMap '{configmap_name}': {e.reason}")
        return False
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error creating ConfigMap '{configmap_name}'")
        logger.debug(f"  Detail: {e}", exc_info=True)
        return False

# Schema init-job orchestration (internal)

def _run_schema_init_job(
    script_path: Path,
    mapping: dict,
    workspace_id: str,
    schema_name: str,
    state: dict,
) -> None:
    """Apply a single K8s init job from *script_path* and wait for its outcome."""
    k8s_job_name = f"postgresql-init-{workspace_id}"
    k8s_client = env.get_kubernetes_client()

    with open(script_path, "r") as f:
        raw_content = f.read()

    yaml_dict = safe_load(Template(raw_content).safe_substitute(mapping))
    try:
        utils.create_from_dict(k8s_client.api_client, yaml_dict, namespace=env.environ_id)
        _wait_and_check_init_job(k8s_job_name, schema_name, state)
    except FailToCreateError as e:
        for inner_exception in e.api_exceptions:
            if inner_exception.status == 409:
                logger.warning(f"  [yellow]⚠[/yellow] [dim]Job [cyan]{k8s_job_name}[/cyan] already exists.[/dim]")
            else:
                logger.error(f"  [bold red]✘[/bold red] Kubernetes API error ({inner_exception.status}): {inner_exception.reason}")
                logger.debug(f"  Detail: {inner_exception.body}")
    except Exception as e:
        logger.error("  [bold red]✘[/bold red] Unexpected error submitting Kubernetes job see 'babylon.log' for details")
        logger.debug(f"  {e}")


def _wait_and_check_init_job(k8s_job_name: str, schema_name: str, state: dict) -> None:
    """Wait for the init job to complete, then inspect its logs."""
    logger.info(f"  [dim]→ Waiting for job [cyan]{k8s_job_name}[/cyan] to complete...[/dim]")
    wait_process = subprocess.run(
        [
            "kubectl",
            "wait",
            "--for=condition=complete",
            "job",
            k8s_job_name,
            f"--namespace={env.environ_id}",
            "--timeout=50s",
        ],
        capture_output=True,
        text=True,
    )
    if wait_process.returncode != 0:
        logger.error(
            f"  [bold red]✘[/bold red] Job '{k8s_job_name}' did not complete within the timeout check 'babylon.log' for details"
        )
        logger.debug(f"  [bold red]✘[/bold red] Job wait output {wait_process.stdout} {wait_process.stderr}")
        return
    logger.debug(f"  Inspecting logs for job '{k8s_job_name}'...")
    _handle_init_job_logs(k8s_job_name, schema_name, state)


def _handle_init_job_logs(k8s_job_name: str, schema_name: str, state: dict) -> None:
    """Fetch init-job logs and update state based on their content."""
    logs_process = subprocess.run(
        ["kubectl", "logs", f"job/{k8s_job_name}", "-n", env.environ_id],
        capture_output=True,
        text=True,
    )
    if logs_process.returncode != 0:
        logger.error(f"  [bold red]✘[/bold red] Failed to retrieve logs for job '{k8s_job_name}'")
        logger.debug(f"  kubectl logs stdout: {logs_process.stdout} stderr: {logs_process.stderr}")
        return

    job_logs = logs_process.stdout or logs_process.stderr
    if "ERROR" in job_logs or "error" in job_logs:
        logger.error("  [bold red]✘[/bold red] Schema initialisation failed the container reported an error")
        logger.debug(f"  Job logs: {job_logs}")
    elif "already exists" in job_logs:
        logger.info(
            f"  [yellow]⚠[/yellow] [dim]Schema [magenta]{schema_name}[/magenta] is already initialised skipping creation[/dim]"
        )
    else:
        logger.info(f"  [bold green]✔[/bold green] Schema [magenta]{schema_name}[/magenta] initialised successfully")
        state["services"]["postgres"]["schema_name"] = schema_name


# Schema teardown public entry point

def destroy_postgres_schema(schema_name: str, state: dict, provider: str = "superset") -> None:
    """Destroy the PostgreSQL schema for a workspace.
    """
    if not schema_name:
        logger.warning("  [yellow]⚠[/yellow] [dim]No schema found ! skipping deletion[/dim]")
        return

    workspace_id_tmp = schema_name.replace("_", "-")
    db_host = get_postgres_host(env.environ_id, provider)
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
    k8s_client = env.get_kubernetes_client()

    with open(destroy_jobs, "r") as f:
        raw_content = f.read()

    yaml_dict = safe_load(Template(raw_content).safe_substitute(mapping))
    logger.info("  [dim]→ Applying kubernetes destroy job...[/dim]")
    try:
        utils.create_from_dict(k8s_client.api_client, yaml_dict, namespace=env.environ_id)
        _wait_and_check_destroy_job(k8s_job_name, schema_name, state)
    except Exception as e:
        logger.error("  [bold red]✘[/bold red] Unexpected error submitting the destroy job see 'babylon.log' for details")
        logger.debug(f"  {e}")

# Schema teardown internal helpers

def _wait_and_check_destroy_job(k8s_job_name: str, schema_name: str, state: dict) -> None:
    """Wait for the destroy job to complete, then inspect its logs."""
    logger.info(f"  [dim]→ Waiting for job [cyan]{k8s_job_name}[/cyan] to complete...[/dim]")
    wait_process = subprocess.run(
        [
            "kubectl",
            "wait",
            "--for=condition=complete",
            "job",
            k8s_job_name,
            f"--namespace={env.environ_id}",
            "--timeout=300s",
        ],
        capture_output=True,
        text=True,
    )
    if wait_process.returncode != 0:
        logger.error(
            f"  [bold red]✘[/bold red] Job '{k8s_job_name}' did not complete within the timeout check 'babylon.log' for details"
        )
        logger.debug(f"  kubectl wait stdout: {wait_process.stdout} stderr: {wait_process.stderr}")
        return

    logger.debug(f"  Inspecting logs for job '{k8s_job_name}'...")
    _handle_destroy_job_logs(k8s_job_name, schema_name, state)


def _handle_destroy_job_logs(k8s_job_name: str, schema_name: str, state: dict) -> None:
    """Fetch destroy-job logs and update state based on their content."""
    logs_process = subprocess.run(
        ["kubectl", "logs", f"job/{k8s_job_name}", "-n", env.environ_id],
        capture_output=True,
        text=True,
    )
    if logs_process.returncode != 0:
        logger.error(f"  [bold red]✘[/bold red] Failed to retrieve logs for job '{k8s_job_name}'")
        logger.debug(f"  kubectl logs stdout: {logs_process.stdout} stderr: {logs_process.stderr}")
        return

    job_logs = logs_process.stdout or logs_process.stderr
    if "ERROR" in job_logs or "error" in job_logs:
        logger.error("  [bold red]✘[/bold red] Schema destruction failed the container reported an error")
        logger.debug(f"  Job logs: {job_logs}")
    elif "does not exist" in job_logs:
        logger.info(f"  [bold green]✔[/bold green] Schema [magenta]{schema_name}[/magenta] does not exist nothing to remove")
        state["services"]["postgres"]["schema_name"] = ""
    else:
        logger.info(f"  [bold green]✔[/bold green] Schema [magenta]{schema_name}[/magenta] destroyed successfully")
        state["services"]["postgres"]["schema_name"] = ""

# K8s resource cleanup 

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
        k8s_client = env.get_kubernetes_client()
    except Exception as e:
        logger.error("  [bold red]✘[/bold red] Failed to initialise Kubernetes client")
        logger.debug(f"  Detail: {e}", exc_info=True)
        return

    _delete_secret(k8s_client, secret_name, namespace)
    _delete_configmap(k8s_client, configmap_name, namespace)


def _delete_secret(k8s_client: client.CoreV1Api, secret_name: str, namespace: str) -> None:
    """Delete a single named Secret, ignoring 404."""
    try:
        logger.info("  [dim]→ Deleting workspace Secret ...[/dim]")
        k8s_client.delete_namespaced_secret(name=secret_name, namespace=namespace)
        logger.info(f"  [bold green]✔[/bold green] Secret [magenta]{secret_name}[/magenta] deleted")
    except client.ApiException as e:
        if e.status == 404:
            logger.warning("  [yellow]⚠[/yellow] [dim]Secret not found already deleted[/dim]")
        else:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete Secret '{secret_name}': {e.reason}")
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error deleting Secret '{secret_name}'")
        logger.debug(f"  Detail: {e}", exc_info=True)


def _delete_configmap(k8s_client: client.CoreV1Api, configmap_name: str, namespace: str) -> None:
    """Delete a single named ConfigMap, ignoring 404."""
    try:
        logger.info("  [dim]→ Deleting workspace ConfigMap ...[/dim]")
        k8s_client.delete_namespaced_config_map(name=configmap_name, namespace=namespace)
        logger.info(f"  [bold green]✔[/bold green] ConfigMap [magenta]{configmap_name}[/magenta] deleted")
    except client.ApiException as e:
        if e.status == 404:
            logger.warning("  [yellow]⚠[/yellow] [dim]ConfigMap not found already deleted[/dim]")
        else:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete ConfigMap '{configmap_name}': {e.reason}")
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error deleting ConfigMap '{configmap_name}'")
        logger.debug(f"  Detail: {e}", exc_info=True)
