from base64 import b64encode
import subprocess
from logging import getLogger
from textwrap import dedent

from click import Abort, echo, style
from cosmotech_api.models.organization_access_control import OrganizationAccessControl
from cosmotech_api.models.organization_security import OrganizationSecurity
from cosmotech_api.models.solution_access_control import SolutionAccessControl
from cosmotech_api.models.solution_security import SolutionSecurity
from cosmotech_api.models.workspace_access_control import WorkspaceAccessControl
from cosmotech_api.models.workspace_security import WorkspaceSecurity
from kubernetes import client, config

from Babylon.utils.environment import Environment

logger = getLogger(__name__)

env = Environment()

# Helper functions for workspace deployment


def validate_inclusion_exclusion(
    include: tuple[str],
    exclude: tuple[str],
) -> bool:
    """Include and exclude command line options cannot be combined and should have correct spelling"""
    if include and exclude:  # cannot combine conflicting options
        echo(style("\n  ✘ Argument Conflict", fg="red", bold=True))
        logger.error("  Cannot use [bold]--include[/bold] and [bold]--exclude[/bold] at the same time")
        raise Abort()

    allowed_values = ("organization", "solution", "workspace", "webapp")
    invalid_items = [i for i in include + exclude if i not in allowed_values]
    if invalid_items:
        echo(style("\n  ✘ Invalid Arguments Detected", fg="red", bold=True))
        # List the errors
        for item in invalid_items:
            logger.error(f"  • [yellow] {item}[/yellow] is not a valid resource type")
        logger.error(f"  Allowed values are: [cyan]{', '.join(allowed_values)}[/cyan]")
        raise Abort()
    return True


def resolve_inclusion_exclusion(
    include: tuple[str],
    exclude: tuple[str],
) -> tuple[bool, bool, bool]:
    """Resolve command line include and exclude.

    Args:
        include (tuple[str]): which objects to include in the deployment
        exclude (tuple[str]): which objects to exclude from the deployment

    Raises:
        ValueError: Error if incompatible options are provided

    Returns:
        tuple[bool, bool, bool]: flags to include organization, solution, workspace
    """
    validate_inclusion_exclusion(include, exclude)
    organization = True
    solution = True
    workspace = True
    webapp = True
    if include:  # if only is specified include by condition
        organization = "organization" in include
        solution = "solution" in include
        workspace = "workspace" in include
        webapp = "webapp" in include
    if exclude:  # if exclude is specified exclude by condition
        organization = "organization" not in exclude
        solution = "solution" not in exclude
        workspace = "workspace" not in exclude
        webapp = "webapp" not in exclude
    return (organization, solution, workspace, webapp)


def diff(
    acl1: OrganizationAccessControl | WorkspaceAccessControl | SolutionAccessControl,
    acl2: OrganizationAccessControl | WorkspaceAccessControl | SolutionAccessControl,
) -> tuple[list[str], list[str], list[str]]:
    """Generate a diff between two access control lists"""
    ids1 = [i.id for i in acl1]
    roles1 = [i.role for i in acl1]
    ids2 = [i.id for i in acl2]
    roles2 = [i.role for i in acl2]
    to_add = [item for item in ids2 if item not in ids1]
    to_delete = [item for item in ids1 if item not in ids2]
    to_update = [item for item in ids1 if item in ids2 and roles1[ids1.index(item)] != roles2[ids2.index(item)]]
    return (to_add, to_delete, to_update)


def update_default_security(
    object_type: str,
    current_security: OrganizationSecurity | WorkspaceSecurity | SolutionSecurity,
    desired_security: OrganizationSecurity | WorkspaceSecurity | SolutionSecurity,
    api_instance,
    object_id: str,
) -> None:
    if desired_security.default != current_security.default:
        try:
            getattr(api_instance, f"update_{object_type}_default_security")(object_id, desired_security.default)
            logger.info(f"  [bold green]✔[/bold green] Updated [magenta]{object_type}[/magenta] default security")
        except Exception as e:
            logger.error(f"  [bold red]✘[/bold red] Failed to update [magenta]{object_type}[/magenta] default security: {e}")


def update_object_security(
    object_type: str,
    current_security: OrganizationSecurity | WorkspaceSecurity | SolutionSecurity,
    desired_security: OrganizationSecurity | WorkspaceSecurity | SolutionSecurity,
    api_instance,
    object_id: list[str],
):
    """Update object security:
    if default security differs from payload
        update object default security
    diff state vs payload
    foreach diff
      delete entries to be removed
      update entries to be changed
      create entries to be added
    """
    update_default_security(object_type, current_security, desired_security, api_instance, object_id)
    (to_add, to_delete, to_update) = diff(current_security.access_control_list, desired_security.access_control_list)
    for entry in desired_security.access_control_list:
        if entry.id in to_add:
            try:
                getattr(api_instance, f"create_{object_type}_access_control")(*object_id, entry)
                logger.info(f"  [bold green]✔[/bold green] Access control for id [magenta]{entry.id}[/magenta] added successfully")
            except Exception as e:
                logger.error(f"  [bold red]✘[/bold red] Failed to add access control for id [magenta]{entry.id}[/magenta]: {e}")
        if entry.id in to_update:
            try:
                getattr(api_instance, f"update_{object_type}_access_control")(*object_id, entry.id, {"role": entry.role})
                logger.info(f"  [bold green]✔[/bold green] Access control for id [magenta]{entry.id}[/magenta] updated successfully")
            except Exception as e:
                logger.error(f"  [bold red]✘[/bold red] Failed to update access control for id [magenta]{entry.id}[/magenta]: {e}")
    for entry_id in to_delete:
        try:
            getattr(api_instance, f"delete_{object_type}_access_control")(*object_id, entry_id)
            logger.info(f"  [bold green]✔[/bold green] Access control for id [magenta]{entry_id}[/magenta] deleted successfully")
        except Exception as e:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete access control for id [magenta]{entry_id}[/magenta]: {e}")


# Helper functions for workspace deployment


def get_postgres_service_host(namespace: str) -> str:
    """Discovers the PostgreSQL service name in a namespace to build its FQDN

    Note: This function assumes PostgreSQL is running within the same Kubernetes cluster.
    External database clusters are not currently supported.
    """
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        services = v1.list_namespaced_service(namespace)

        for svc in services.items:
            if "postgresql" in svc.metadata.name or svc.metadata.labels.get("app.kubernetes.io/name") == "postgresql":
                logger.info(f"  [dim]→ Found PostgreSQL service {svc.metadata.name}[/dim]")
                return f"{svc.metadata.name}.{namespace}.svc.cluster.local"

        return f"postgresql.{namespace}.svc.cluster.local"
    except Exception as e:
        logger.warning("  [bold yellow]⚠[/bold yellow] Service discovery failed ! default will be used.")
        logger.debug(f"  Exception details: {e}", exc_info=True)
        return f"postgresql.{namespace}.svc.cluster.local"


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
    except client.ApiException as e:
        if e.status == 409:
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
            logger.warning(
                f"  [yellow]⚠[/yellow] [dim]ConfigMap [magenta]{configmap_name}[/magenta] already exists[/dim]"
            )
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
        logger.info(f"  [dim]→ Deleting workspace Secret ...[/dim]")
        v1.delete_namespaced_secret(name=secret_name, namespace=namespace)
        logger.info(f"  [bold green]✔[/bold green] Secret [magenta]{secret_name}[/magenta] deleted")
    except client.ApiException as e:
        if e.status == 404:
            logger.warning(f"  [yellow]⚠[/yellow] [dim]Secret not found (already deleted)[/dim]")
        else:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete secret {secret_name}: {e.reason}")
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error deleting secret {secret_name}")
        logger.debug(f"  Detail: {e}", exc_info=True)

    # --- Delete ConfigMap ---
    try:
        logger.info(f"  [dim]→ Deleting workspace ConfigMap ...[/dim]")
        v1.delete_namespaced_config_map(name=configmap_name, namespace=namespace)
        logger.info(f"  [bold green]✔[/bold green] ConfigMap [magenta]{configmap_name}[/magenta] deleted")
    except client.ApiException as e:
        if e.status == 404:
            logger.warning(
                f"  [yellow]⚠[/yellow] [dim]ConfigMap not found (already deleted)[/dim]"
            )
        else:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete ConfigMap {configmap_name}: {e.reason}")
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error deleting ConfigMap {configmap_name}")
        logger.debug(f"  Detail: {e}", exc_info=True)


# Helper functions for web application deployment


def dict_to_tfvars(payload: dict) -> str:
    """Convert a dictionary to Terraform HCL tfvars format (key = "value").

    Currently handles simple data structures:
    - Booleans: converted to lowercase (true/false)
    - Numbers: integers and floats as-is
    - Strings: wrapped in double quotes

    Note: Complex nested structures (lists, dicts) are not yet supported.
    This is sufficient for current WebApp tfvars which only use simple scalar values.

    Args:
        payload (dict): Dictionary with simple key-value pairs

    Returns:
        str: Terraform HCL formatted variable assignments
    """
    lines = []
    for key, value in payload.items():
        if isinstance(value, bool):
            lines.append(f"{key} = {str(value).lower()}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key} = {value}")
        else:
            lines.append(f'{key} = "{value}"')
    return "\n".join(lines)


def _run_terraform_process(executable, cwd, payload, state):
    """Helper function to reduce the size of the main function (Clean Code)"""
    try:
        process = subprocess.Popen(executable, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        # Color mapping to avoid if/else statements in the loop
        status_colors = {
            "Initializing": "white",
            "Upgrading": "white",
            "Finding": "white",
            "Refreshing": "white",
            "Success": "green",
            "complete": "green",
            "Resources:": "green",
            "Error": "red",
            "error": "red",
        }

        for line in process.stdout:
            clean_line = line.strip()
            if not clean_line:
                continue

            color = next((status_colors[k] for k in status_colors if k in clean_line), "white")
            is_bold = color == "red"
            echo(style(f"   {clean_line}", fg=color, bold=is_bold))

        if process.wait() == 0:
            _finalize_deployment(payload, state)
        else:
            logger.error("  [bold red]✘[/bold red] Deployment failed")

    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Execution error: {e}")


def _finalize_deployment(payload, state):
    """Handles the update of the final state"""
    webapp_name = payload.get("webapp_name")
    url = f"https://{payload.get('cluster_name')}.{payload.get('domain_zone')}/tenant-{payload.get('tenant')}/webapp-{webapp_name}"

    services = state.setdefault("services", {})
    services["webapp"] = {"webapp_name": f"webapp-{webapp_name}", "webapp_url": url}

    logger.info(f"  [bold green]✔[/bold green] WebApp [bold white]{webapp_name}[/bold white] deployed")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
