"""
Power BI helpers for dashboard deployment.
"""

from base64 import b64decode
from copy import deepcopy
from io import StringIO
from logging import getLogger
from pathlib import Path
from re import compile as re_compile
from typing import Any

from kubernetes.client.exceptions import ApiException
from ruamel.yaml import YAML as _RYAML
from yaml import safe_load

from Babylon.commands.macro.helpers.workspace.api_cosmotech_helper import update_workspace
from Babylon.commands.powerbi.dataset.services.powerbi_api_svc import AzurePowerBIDatasetService
from Babylon.commands.powerbi.dataset.services.powerbi_params_svc import AzurePowerBIParamsService
from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import AzurePowerBIReportService
from Babylon.commands.powerbi.workspace.services.powerb__worskapce_users_svc import (
    AzurePowerBIWorkspaceUserService,
)
from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import AzurePowerBIWorkspaceService
from Babylon.utils.credentials import get_azure_token, get_current_user_email, get_powerbi_token
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.string import slugify_tag

logger = getLogger(__name__)
env = Environment()

# Matches Power BI template variables such as:
# ${powerbi['workspace_id']} and ${powerbi['reports']['scenario_view']}.
_POWERBI_TEMPLATE_VAR_RE = re_compile(
    r"\$\{\s*powerbi\[\s*['\"]([a-zA-Z0-9_]+)['\"]\s*\]"
    r"(?:\[\s*['\"]([a-zA-Z0-9_]+)['\"]\s*\])?\s*\}"
)

# Dataset parameter name defined in the PBIX file.
_SCHEMA_PARAM_ID = "Schema"

# groupUserAccessRight to grant the WebApp's Power BI App Registration.
_WEBAPP_APP_ACCESS_RIGHT = "Member"


# Workspace resolution & template rendering


def _update_workspace_with_powerbi_ids(api_instance, api_section, file_content, state) -> bool:
    """Re-render the Workspace template with persisted Power BI IDs."""
    ext_args = build_powerbi_ext_args(fallback_empty=False)
    content = env.fill_template(data=file_content, state=state, ext_args=ext_args or None)
    payload = content.get("spec", {}).get("payload", {})
    return update_workspace(api_instance, api_section, payload)


def _ensure_powerbi_workspace(powerbi_token: str, powerbi_config: dict) -> str | None:
    """Ensure the target Power BI workspace exists and return its ID."""

    workspace_name = powerbi_config.get("name", "")
    if not workspace_name:
        logger.error("  [bold red]✘[/bold red] PowerBI workspace name is mandatory in the dashboards sidecar")
        return None

    workspace_service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token)

    for workspace in workspace_service.get_all() or []:
        if workspace.get("name") == workspace_name:
            return workspace.get("id")

    logger.info(f"  [dim]→ Creating Power BI workspace '{workspace_name}'...[/dim]")
    created = workspace_service.create(name=workspace_name)
    if not created:
        logger.error(f"  [bold red]✘[/bold red] Failed to create Power BI workspace '{workspace_name}'")
        return None
    return created.get("id")


# WebApp Power BI App Registration lookup (Kubernetes secret + Microsoft Graph)


def _get_webapp_powerbi_client_id(state: dict) -> str | None:
    """Get the WebApp Power BI App Registration client ID from Kubernetes secret."""
    variables = env.get_variables()
    webapp_name = variables.get("webapp_name")

    if not webapp_name:
        webapp_name = state.get("services", {}).get("webapp", {}).get("webapp_name", "")
        webapp_name = webapp_name.removeprefix("webapp-")

    if not webapp_name:
        logger.debug("  WebApp name could not be resolved, skipping Power BI App Registration lookup")
        return None

    secret_name = f"webapp-{webapp_name}-powerbi-client"

    try:
        k8s_client = env.get_kubernetes_client()
        secret = k8s_client.read_namespaced_secret(
            name=secret_name,
            namespace=env.environ_id,
        )
    except ApiException as exc:
        if exc.status == 404:
            logger.debug(f"  Secret '{secret_name}' not found in namespace '{env.environ_id}'")
        else:
            logger.warning(f"  [yellow]⚠[/yellow] Failed to read Secret '{secret_name}': {exc.reason}")
        return None
    except Exception as exc:
        logger.warning(f"  [yellow]⚠[/yellow] Failed to read Secret '{secret_name}': {exc}")
        return None

    if not secret.data:
        logger.warning(
            f"  [yellow]⚠[/yellow] Secret '{secret_name}' is empty, WebApp Power BI App Registration permission sync will be skipped"
        )
        return None

    client_id = secret.data.get("client_id")
    if not client_id:
        logger.warning(f"  [yellow]⚠[/yellow] Secret '{secret_name}' has no 'client_id' key")
        return None

    return b64decode(client_id).decode("utf-8")


def _get_webapp_powerbi_service_principal_id(state: dict) -> str | None:
    """Get the Microsoft Entra Service Principal Object ID for the WebApp."""

    client_id = _get_webapp_powerbi_client_id(state)
    if not client_id:
        return None

    graph_token = get_azure_token(scope="https://graph.microsoft.com/.default")
    if not graph_token:
        logger.warning(
            "  [yellow]⚠[/yellow] Failed to acquire a Microsoft Graph token, "
            "cannot resolve the WebApp Power BI Service Principal Object ID"
        )
        return None

    url = f"https://graph.microsoft.com/v1.0/servicePrincipals?$filter=appId eq '{client_id}'"

    response = oauth_request(url, graph_token)
    if response is None:
        logger.warning(f"  [yellow]⚠[/yellow] Failed to look up Service Principal for client_id '{client_id}' via Microsoft Graph")
        return None

    service_principals = response.json().get("value") or []
    if not service_principals:
        logger.warning(f"  [yellow]⚠[/yellow] No Service Principal found in Microsoft Graph for client_id '{client_id}'")
        return None

    return service_principals[0].get("id")


# Report discovery: turn the `reports` config into a flat list of report
# entries (name, path, tag, parameters).


def _discover_powerbi_reports(reports_config: dict, deploy_dir: Path) -> list[dict]:
    """Build report entries by scanning a folder for .pbix files."""

    rel_path = reports_config.get("path") or ""
    if not rel_path:
        logger.warning("  [yellow]⚠[/yellow] 'reports.path' is required when using folder-based Power BI report discovery")
        return []

    folder = Path(rel_path) if Path(rel_path).is_absolute() else (Path(deploy_dir).resolve() / rel_path)

    if not folder.is_dir():
        logger.error(f"  [bold red]✘[/bold red] Power BI reports folder not found: {folder}")
        return []

    shared_parameters = reports_config.get("parameters") or []

    discovered: list[dict] = []
    for pbix_path in sorted(folder.glob("*.pbix")):
        name = pbix_path.stem
        discovered.append(
            {
                "name": name,
                "path": str(pbix_path),
                "tag": slugify_tag(name),
                "parameters": list(shared_parameters),
            }
        )

    if not discovered:
        logger.warning(f"  [yellow]⚠[/yellow] No .pbix files found in Power BI reports folder: {folder}")

    return discovered


def _resolve_powerbi_reports(reports: list | dict, deploy_dir: Path) -> list[dict]:
    """Normalize reports configuration into a flat list of report entries."""

    if isinstance(reports, dict):
        return _discover_powerbi_reports(reports, deploy_dir)

    if isinstance(reports, list):
        resolved: list[dict] = []
        for entry in reports:
            if isinstance(entry, dict) and entry.get("path") and not entry.get("name"):
                # Folder-discovery spec expressed as a YAML list item.
                resolved.extend(_discover_powerbi_reports(entry, deploy_dir))
            else:
                resolved.append(entry)
        return resolved

    logger.warning(
        "  [yellow]⚠[/yellow] Unsupported 'reports' configuration type expected a list of reports or a {path, parameters} mapping"
    )
    return []


# Deployment orchestration: authenticate, resolve/create the workspace,
# upload each discovered report and sync workspace permissions.


def deploy_powerbi(
    reports: list,
    state: dict,
    powerbi_config: dict,
    deploy_dir: Path,
) -> tuple[bool, set[str]]:
    """Authenticate with Power BI, upload dashboard .pbix reports, take ownership
    of their datasets, update dataset parameters, and sync workspace permissions.
    """
    resolved_reports = _resolve_powerbi_reports(reports, deploy_dir)
    valid_reports = [r for r in resolved_reports if isinstance(r, dict) and r.get("name") and r.get("path")]
    if not valid_reports:
        logger.warning("  [yellow]⚠[/yellow] No valid report entries each entry must have 'name' and 'path'")
        return True, set()

    powerbi_token = get_powerbi_token()
    if not powerbi_token:
        logger.error("  [bold red]✘[/bold red] Failed to retrieve Power BI token")
        return False, set()

    workspace_id = _ensure_powerbi_workspace(powerbi_token, powerbi_config)
    if not workspace_id:
        return False, set()

    _update_powerbi_variable(["workspace_id"], workspace_id)

    logger.info(f"  [dim]→ Deploying {len(valid_reports)} dashboard report(s) to Power BI workspace '{workspace_id}'...[/dim]")

    services = state.get("services")

    report_service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=services)
    dataset_service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=services)
    params_service = AzurePowerBIParamsService(powerbi_token=powerbi_token, state=services)

    abs_deploy_dir = Path(deploy_dir).resolve()
    schema_name = _resolve_postgres_schema_name(state)
    writer_username, writer_password = _resolve_postgres_writer_credentials()

    all_ok = True
    for report in valid_reports:
        if not _upload_powerbi_report(
            report_service=report_service,
            dataset_service=dataset_service,
            params_service=params_service,
            workspace_id=workspace_id,
            report=report,
            abs_deploy_dir=abs_deploy_dir,
            schema_name=schema_name,
            writer_username=writer_username,
            writer_password=writer_password,
        ):
            all_ok = False

    if not _sync_powerbi_workspace_permissions(powerbi_token, workspace_id, powerbi_config, state):
        all_ok = False

    return all_ok, set()


# PostgreSQL schema/credentials resolution (used to feed dataset parameters
# and gateway credentials when uploading a report).


def _resolve_postgres_schema_name(state: dict) -> str | None:
    """Derive the PostgreSQL schema name from the workspace ID."""

    workspace_id = state.get("services", {}).get("api", {}).get("workspace_id") or ""

    return workspace_id.replace("-", "_") if workspace_id else None


def _resolve_postgres_writer_credentials() -> tuple[str | None, str | None]:
    """Resolve the PostgreSQL writer credentials for Power BI datasets."""

    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    if not api_config:
        logger.warning(
            "  [yellow]⚠[/yellow] Could not read 'postgresql-cosmotechapi' Secret dataset credentials update will be skipped"
        )
        return None, None

    writer_password = api_config.get("writer-password")
    if not writer_password:
        logger.warning(
            "  [yellow]⚠[/yellow] Writer password missing in 'postgresql-cosmotechapi' Secret "
            "dataset credentials update will be skipped"
        )
        return None, None

    tenant = env.environ_id
    clean_prefix = tenant.replace("-", "_")
    writer_username = f"{clean_prefix}_cosmotech_api_writer"

    return writer_username, writer_password


# Single report upload: PBIX import, report ID persistence, dataset
# ownership/parameters/credentials.


def _upload_powerbi_report(
    report_service: AzurePowerBIReportService,
    dataset_service: AzurePowerBIDatasetService,
    params_service: AzurePowerBIParamsService,
    workspace_id: str,
    report: dict,
    abs_deploy_dir: Path,
    schema_name: str | None = None,
    writer_username: str | None = None,
    writer_password: str | None = None,
) -> bool:
    """Upload a Power BI report, persist its ID, and update its datasets."""

    name: str = report.get("name", "")
    rel_path: str = report.get("path", "")

    pbix_path = Path(rel_path).resolve() if Path(rel_path).is_absolute() else (abs_deploy_dir / rel_path).resolve()

    if not pbix_path.exists():
        logger.error(f"  [bold red]✘[/bold red] Report file not found: {pbix_path}")
        return False

    tag = _prepare_report_tag(report)

    params = _merge_schema_param(
        report.get("parameters") or [],
        schema_name,
    )

    try:
        import_data, new_report = report_service.upload(
            workspace_id=workspace_id,
            pbix_filename=pbix_path,
            report_name=name,
            report_type="dashboard_view",
            override=True,
        )
    except Exception as exp:
        logger.error(f"  [bold red]✘[/bold red] Failed to upload report '{name} to Power BI': {exp}")
        return False

    logger.info(f"  [bold green]✔[/bold green] Report [cyan]{name}[/cyan] uploaded to Power BI")

    report_id = new_report.get("reportId") if isinstance(new_report, dict) else None
    if report_id and tag:
        _update_powerbi_variable(["reports", tag], report_id)
        logger.info(f"  [bold green]✔[/bold green] Report id {report_id} saved in 'Variables.yaml' file")
    elif not tag:
        logger.warning(f"  [yellow]⚠[/yellow] Report '{name}' produced an empty tag skipping id persistence")
    else:
        logger.warning(f"  [yellow]⚠[/yellow] Report '{name}' upload did not return a reportId")

    for dataset in import_data.get("datasets", []) or []:
        dataset_id = dataset.get("id")
        if not dataset_id:
            continue

        # Take ownership of the dataset to allow parameter updates and credential changes.
        dataset_service.take_over(workspace_id=workspace_id, dataset_id=dataset_id)

        # Update dataset parameters if any are defined in the report configuration.
        if params:
            params_service.update(workspace_id=workspace_id, params=params, dataset_id=dataset_id)

        # Update dataset credentials if writer credentials are available.
        if writer_username and writer_password:
            dataset_service.update_credentials(
                workspace_id=workspace_id,
                dataset_id=dataset_id,
                username=writer_username,
                password=writer_password,
            )

    logger.info(f"  [bold green]✔[/bold green] Report [cyan]{name}[/cyan] successfully imported")
    return True


# Workspace permissions sync (add/update/remove + WebApp App Registration
# auto-grant).


def _sync_powerbi_workspace_permissions(
    powerbi_token: str,
    workspace_id: str,
    powerbi_config: dict,
    state: dict,
) -> bool:
    """Synchronize Power BI workspace permissions."""

    permissions = list(powerbi_config.get("permissions", []) or [])

    user_service = AzurePowerBIWorkspaceUserService(
        powerbi_token=powerbi_token,
        state=state.get("services"),
    )

    existing_users = user_service.get_all(workspace_id=workspace_id) or []

    existing_rights = {user["identifier"]: user.get("groupUserAccessRight") for user in existing_users if user.get("identifier")}

    # Automatically grant Member access to the WebApp Power BI App Registration.
    webapp_object_id = _get_webapp_powerbi_service_principal_id(state)

    if webapp_object_id and not any(permission.get("identifier") == webapp_object_id for permission in permissions):
        permissions.append(
            {
                "identifier": webapp_object_id,
                "rights": _WEBAPP_APP_ACCESS_RIGHT,
                "type": "App",
            }
        )

        # Only log when this actually changes something (new grant or right
        # change) not on every idempotent re-run once access is already set.
        if existing_rights.get(webapp_object_id) != _WEBAPP_APP_ACCESS_RIGHT:
            logger.info(
                f"  [dim]→ Detected WebApp Power BI App Registration "
                f"object_id: {webapp_object_id} will grant it "
                f"'{_WEBAPP_APP_ACCESS_RIGHT}' access to the workspace Power BI[/dim]"
            )

    if not permissions:
        return True

    existing_identifiers = set(existing_rights)
    desired_identifiers = {permission["identifier"] for permission in permissions if permission.get("identifier")}

    current_user_email = (get_current_user_email(powerbi_token) or "").lower()

    all_ok = _sync_powerbi_permission_entries(
        user_service=user_service,
        workspace_id=workspace_id,
        permissions=permissions,
        existing_rights=existing_rights,
        current_user_email=current_user_email,
    )

    remove_ok = _remove_powerbi_workspace_permissions(
        user_service=user_service,
        workspace_id=workspace_id,
        existing_identifiers=existing_identifiers,
        desired_identifiers=desired_identifiers,
        current_user_email=current_user_email,
    )

    return all_ok and remove_ok


def _sync_powerbi_permission_entries(
    user_service: AzurePowerBIWorkspaceUserService,
    workspace_id: str,
    permissions: list[dict],
    existing_rights: dict[str, str],
    current_user_email: str,
) -> bool:
    """Add missing permissions and update permissions with changed rights."""

    all_ok = True

    for permission in permissions:
        identifier = permission.get("identifier")
        rights = permission.get("rights")
        principal_type = permission.get("type")

        if not identifier or not rights or not principal_type:
            logger.warning(f"  [yellow]⚠[/yellow] Skipping incomplete permission entry: {permission}")
            continue

        if current_user_email and identifier.lower() == current_user_email:
            logger.warning(
                f"  [yellow]⚠[/yellow] Skipping '{identifier}' "
                "Power BI doesn't allow a user to update their own "
                "workspace permissions via the API"
            )
            continue

        try:
            if identifier not in existing_rights:
                logger.info(f"  [dim]→ Adding Power BI permissions for '{identifier}'...[/dim]")
                user_service.add(
                    workspace_id=workspace_id,
                    right=rights,
                    email=identifier,
                    type=principal_type,
                )

            elif existing_rights[identifier] != rights:
                logger.info(f"  [dim]→ Updating Power BI permissions for '{identifier}'...[/dim]")
                user_service.update(
                    workspace_id=workspace_id,
                    right=rights,
                    email=identifier,
                    type=principal_type,
                )

        except Exception as exc:
            logger.error(f"  [bold red]✘[/bold red] Failed to sync permissions for '{identifier}': {exc}")
            all_ok = False

    return all_ok


def _remove_powerbi_workspace_permissions(
    user_service: AzurePowerBIWorkspaceUserService,
    workspace_id: str,
    existing_identifiers: set[str],
    desired_identifiers: set[str],
    current_user_email: str,
) -> bool:
    """Remove workspace permissions that are no longer desired."""

    all_ok = True

    identifiers_to_remove = existing_identifiers - desired_identifiers

    for identifier in identifiers_to_remove:
        if current_user_email and identifier.lower() == current_user_email:
            logger.warning(
                f"  [yellow]⚠[/yellow] Skipping removal of '{identifier}' "
                "Power BI doesn't allow a user to update their own "
                "workspace permissions via the API"
            )
            continue

        try:
            logger.info(f"  [dim]→ Removing Power BI permissions for '{identifier}'...[/dim]")

            user_service.delete(
                workspace_id=workspace_id,
                email=identifier,
                force_validation=True,
            )

        except Exception as exc:
            logger.error(f"  [bold red]✘[/bold red] Failed to remove permissions for '{identifier}': {exc}")
            all_ok = False

    return all_ok


# Report metadata & parameter helpers (tag/params generation).
# The tag generated here is the same key exposed to templates as
# ``powerbi['reports'][tag]``.


def _merge_schema_param(params: list[dict], schema_name: str | None) -> list[dict]:
    """Add the auto-computed ``Schema`` parameter when not explicitly defined."""
    if not schema_name:
        return params

    schema_id = _SCHEMA_PARAM_ID
    has_schema = any((p.get("id") or "").strip().lower() == schema_id for p in params)

    if has_schema:
        return params

    return [*params, {"id": _SCHEMA_PARAM_ID, "value": schema_name}]


def _prepare_report_tag(report: dict) -> str:
    """Derive the tag used to expose the report as ``powerbi['reports'][tag]``."""
    name = report.get("name", "")
    return report.get("tag") or slugify_tag(name)


def _update_powerbi_variable(path: list[str], value: str) -> bool:
    """Persist a value under ``powerbi.<path...>`` in the variables file."""
    if not env.variable_files:
        logger.warning("  [yellow]⚠[/yellow] No variable files configured cannot persist Power BI id")
        return False

    variables_path = Path(env.variable_files[0])
    if not variables_path.is_file():
        logger.error(f"  [bold red]✘[/bold red] Variables file not found: {variables_path}")
        return False

    try:
        ry = _RYAML()
        ry.preserve_quotes = True
        ry.width = 4096
        ry.default_flow_style = False

        data = ry.load(variables_path.read_text(encoding="utf-8")) or {}

        powerbi = data.get("powerbi")
        if not isinstance(powerbi, dict):
            powerbi = data["powerbi"] = {}

        node = powerbi
        for key in path[:-1]:
            child = node.get(key)
            if not isinstance(child, dict):
                child = node[key] = {}

            node = child

        node[path[-1]] = value

        buffer = StringIO()
        ry.dump(data, buffer)
        variables_path.write_text(buffer.getvalue(), encoding="utf-8", newline="\n")
        return True
    except OSError as exc:
        logger.error(f"  [bold red]✘[/bold red] File system error updating '{variables_path.name}': {exc}")
    except Exception as exc:
        logger.error(f"  [bold red]✘[/bold red] YAML error updating '{variables_path.name}': {exc}")
    return False


def build_powerbi_ext_args(template_content: str = "", fallback_empty: bool = False) -> dict:
    """Build the ``{"powerbi": {...}}`` ext_args dict used for template rendering."""
    powerbi_data: dict[str, Any] = {}
    if env.variable_files:
        try:
            variables = safe_load(Path(env.variable_files[0]).read_text(encoding="utf-8")) or {}
        except OSError:
            variables = {}
        existing = variables.get("powerbi")
        if isinstance(existing, dict):
            powerbi_data = deepcopy(existing)

    if fallback_empty and template_content:
        for top_key, sub_key in _POWERBI_TEMPLATE_VAR_RE.findall(template_content):
            if not sub_key:
                powerbi_data.setdefault(top_key, "")
                continue

            bucket = powerbi_data.get(top_key)
            if not isinstance(bucket, dict):
                bucket = powerbi_data[top_key] = {}

            bucket.setdefault(sub_key, "")

    return {"powerbi": powerbi_data} if powerbi_data else {}


# Teardown: delete every Power BI resource created for a workspace (used by
# the Destroy Macro Command). Deletion order: datasets -> workspace (the
# workspace deletion cascades any reports still referencing them)


def _clear_powerbi_variables() -> None:
    """Clear persisted Power BI workspace and report IDs."""

    _update_powerbi_variable(["workspace_id"], "")
    _update_powerbi_variable(["reports"], {})


def _destroy_powerbi_datasets(dataset_service: AzurePowerBIDatasetService, workspace_id: str) -> bool:
    """Delete all datasets in a Power BI workspace."""

    datasets = dataset_service.get_all(workspace_id=workspace_id) or []
    if not datasets:
        logger.info("  [dim]→ No Power BI dataset(s) found to delete[/dim]")
        return True

    all_ok = True
    for dataset in datasets:
        dataset_id = dataset.get("id")
        if not dataset_id:
            continue
        try:
            dataset_service.delete(workspace_id=workspace_id, force_validation=True, dataset_id=dataset_id)
            logger.info(f"  [bold green]✔[/bold green] Dataset [cyan]{dataset_id}[/cyan] deleted")
        except Exception as exc:
            logger.error(f"  [bold red]✘[/bold red] Failed to delete dataset '{dataset_id}': {exc}")
            all_ok = False

    return all_ok


def _destroy_powerbi_workspace(workspace_service: AzurePowerBIWorkspaceService, workspace_id: str) -> bool:
    """Delete a Power BI workspace; treat an already-deleted workspace as success."""

    existing_workspaces = workspace_service.get_all() or []
    if not any(w.get("id") == workspace_id for w in existing_workspaces):
        logger.info(f"  [dim]→ Power BI workspace '{workspace_id}' already deleted[/dim]")
        return True

    try:
        result = workspace_service.delete(workspace_id=workspace_id, force_validation=True)
    except Exception as exc:
        logger.error(f"  [bold red]✘[/bold red] Failed to delete Power BI workspace '{workspace_id}': {exc}")
        return False

    if result is None or (hasattr(result, "has_failed") and result.has_failed()):
        logger.error(f"  [bold red]✘[/bold red] Failed to delete Power BI workspace '{workspace_id}'")
        return False

    return True


def destroy_powerbi_assets(state: dict) -> bool:
    """Delete Power BI datasets and workspace resources for the current deployment."""

    variables = env.get_variables()
    powerbi_vars = variables.get("powerbi") or {}
    workspace_id = powerbi_vars.get("workspace_id")

    if not workspace_id:
        logger.info("  [dim]→ No Power BI workspace found in variables ! nothing to destroy[/dim]")
        return True

    powerbi_token = get_powerbi_token()
    if not powerbi_token:
        logger.error("  [bold red]✘[/bold red] Failed to retrieve Power BI token skipping Power BI cleanup")
        return False

    services = state.get("services")
    dataset_service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=services)
    workspace_service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token, state=services)

    logger.info(f"  [dim]→ Destroying Power BI resources in workspace '{workspace_id}'...[/dim]")

    datasets_ok = _destroy_powerbi_datasets(dataset_service, workspace_id)
    workspace_ok = _destroy_powerbi_workspace(workspace_service, workspace_id)

    if datasets_ok and workspace_ok:
        _clear_powerbi_variables()
        return True

    logger.warning(
        f"  [yellow]⚠[/yellow] Power BI cleanup for workspace '{workspace_id}' was partially unsuccessful "
        "re-run the destroy command to retry"
    )
    return False
