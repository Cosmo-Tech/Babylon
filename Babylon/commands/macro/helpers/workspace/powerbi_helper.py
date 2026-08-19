"""
Power BI helpers for dashboard deployment.
"""

from copy import deepcopy
from io import StringIO
from logging import getLogger
from pathlib import Path
from re import compile as re_compile
from re import sub as re_sub

from ruamel.yaml import YAML as _RYAML
from yaml import safe_load
from typing import Any
from Babylon.commands.powerbi.dataset.services.powerbi_api_svc import AzurePowerBIDatasetService
from Babylon.commands.powerbi.dataset.services.powerbi_params_svc import AzurePowerBIParamsService
from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import AzurePowerBIReportService
from Babylon.commands.powerbi.workspace.services.powerb__worskapce_users_svc import (
    AzurePowerBIWorkspaceUserService,
)
from Babylon.commands.macro.helpers.workspace.api_cosmotech_helper import update_workspace

from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import AzurePowerBIWorkspaceService
from Babylon.utils.credentials import get_powerbi_token
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()

# Short-hand report types supported by the sidecar.
_REPORT_TYPE_ALIASES = {
    "scenario": "scenario_view",
    "dashboard": "dashboard_view",
}

# Matches Power BI template variables such as:
# ${powerbi['workspace_id']} and ${powerbi['scenario_view']['report_id']}.
_POWERBI_TEMPLATE_VAR_RE = re_compile(
    r"\$\{\s*powerbi\[\s*['\"]([a-zA-Z0-9_]+)['\"]\s*\]"
    r"(?:\[\s*['\"]([a-zA-Z0-9_]+)['\"]\s*\])?\s*\}"
)

# Dataset parameter name defined in the PBIX file.
_SCHEMA_PARAM_ID = "Schema"

def _update_workspace_with_powerbi_ids(api_instance, api_section, file_content, state) -> bool:
    """Re-render the Workspace template with persisted Power BI IDs."""
    ext_args = build_powerbi_ext_args(fallback_empty=False)
    content = env.fill_template(data=file_content, state=state, ext_args=ext_args or None)
    payload = content.get("spec", {}).get("payload", {})
    return update_workspace(api_instance, api_section, payload)

def _resolve_powerbi_workspace_id(powerbi_token: str, powerbi_config: dict) -> str | None:
    """Resolve the target Power BI workspace ID, creating it if necessary."""
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


def deploy_powerbi(
    reports: list,
    state: dict,
    powerbi_config: dict,
    deploy_dir: Path,
) -> tuple[bool, set[str]]:
    """Authenticate with Power BI, upload dashboard .pbix reports, take ownership
    of their datasets, update dataset parameters, and sync workspace permissions.
    """
    valid_reports = [r for r in reports if isinstance(r, dict) and r.get("name") and r.get("path")]
    if not valid_reports:
        logger.warning("  [yellow]⚠[/yellow] No valid report entries each entry must have 'name' and 'path'")
        return True, set()

    powerbi_token = get_powerbi_token()
    if not powerbi_token:
        logger.error("  [bold red]✘[/bold red] Failed to retrieve Power BI token")
        return False, set()

    workspace_id = _resolve_powerbi_workspace_id(powerbi_token, powerbi_config)
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


def _resolve_postgres_schema_name(state: dict) -> str | None:
    """Derive the PostgreSQL schema name from the workspace ID."""
    workspace_id = state.get("services", {}).get("api", {}).get("workspace_id") or ""

    return workspace_id.replace("-", "_") if workspace_id else None


def _resolve_postgres_writer_credentials() -> tuple[str | None, str | None]:
    """Resolve the PostgreSQL writer credentials for Power BI datasets."""

    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    if not api_config:
        logger.warning(
            "  [yellow]⚠[/yellow] Could not read 'postgresql-cosmotechapi' Secret "
            "dataset credentials update will be skipped"
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

    pbix_path = (
        Path(rel_path).resolve()
        if Path(rel_path).is_absolute()
        else (abs_deploy_dir / rel_path).resolve()
    )

    if not pbix_path.exists():
        logger.error(f"  [bold red]✘[/bold red] Report file not found: {pbix_path}")
        return False

    report_type = _normalize_report_type(report.get("type", ""))
    tag = report.get("tag") or _sanitize_tag(name)

    params = _merge_schema_param(
        report.get("parameters") or [],
        schema_name,
    )

    try:
        import_data, new_report = report_service.upload(
            workspace_id=workspace_id,
            pbix_filename=pbix_path,
            report_name=name,
            report_type=report_type,
            override=True,
        )
    except Exception as exp:
        logger.error(f"  [bold red]✘[/bold red] Failed to upload report '{name} to Power BI': {exp}")
        return False

    logger.info(f"  [bold green]✔[/bold green] Report [cyan]{name}[/cyan] uploaded to Power BI")

    report_id = new_report.get("reportId") if isinstance(new_report, dict) else None
    if report_id and tag:
        _update_powerbi_variable([report_type, tag], report_id)
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


def _sync_powerbi_workspace_permissions(
    powerbi_token: str,
    workspace_id: str,
    powerbi_config: dict,
    state: dict,
) -> bool:
    """Synchronize Power BI workspace permissions."""
    permissions: list[dict] = powerbi_config.get("permissions", []) or []
    if not permissions:
        return True

    user_service = AzurePowerBIWorkspaceUserService(
        powerbi_token=powerbi_token,
        state=state.get("services"),
    )
    existing_users = user_service.get_all(workspace_id=workspace_id) or []

    existing_identifiers = {user.get("identifier") for user in existing_users if user.get("identifier")}
    desired_identifiers = {permission.get("identifier") for permission in permissions if permission.get("identifier")}

    all_ok = True

    for entry in permissions:
        identifier = entry.get("identifier")
        rights = entry.get("rights")
        principal_type = entry.get("type")

        if not identifier or not rights or not principal_type:
            logger.warning(f"  [yellow]⚠[/yellow] Skipping incomplete permission entry: {entry}")
            continue

        try:
            if identifier in existing_identifiers:
                logger.info(f"  [dim]→ Updating Power BI permissions for '{identifier}'...[/dim]")
                user_service.update(workspace_id=workspace_id, right=rights, email=identifier, type=principal_type)
            else:
                logger.info(f"  [dim]→ Adding Power BI permissions for '{identifier}'...[/dim]")
                user_service.add(workspace_id=workspace_id, right=rights, email=identifier, type=principal_type)
        except Exception as exp:
            logger.error(f"  [bold red]✘[/bold red] Failed to sync permissions for '{identifier}': {exp}")
            all_ok = False

    for identifier in existing_identifiers - desired_identifiers:
        try:
            logger.info(f"  [dim]→ Removing Power BI permissions for '{identifier}'...[/dim]")
            user_service.delete(workspace_id=workspace_id, email=identifier, force_validation=True)
        except Exception as exp:
            logger.error(f"  [bold red]✘[/bold red] Failed to remove permissions for '{identifier}': {exp}")
            all_ok = False

    return all_ok

def _merge_schema_param(params: list[dict], schema_name: str | None) -> list[dict]:
    """Add the auto-computed ``Schema`` parameter when not explicitly defined."""
    if not schema_name:
        return params

    schema_id = _SCHEMA_PARAM_ID
    has_schema = any((p.get("id") or "").strip().lower() == schema_id for p in params)

    if has_schema:
        return params

    return [*params, {"id": _SCHEMA_PARAM_ID, "value": schema_name}]


def _normalize_report_type(raw_type: str) -> str:
    """Normalize a report type to the Power BI service value."""
    normalized = (raw_type or "").strip().lower()

    if normalized in _REPORT_TYPE_ALIASES:
        return _REPORT_TYPE_ALIASES[normalized]
    return normalized if normalized in {"scenario_view", "dashboard_view"} else "dashboard_view"


def _sanitize_tag(value: str) -> str:
    """Return a lowercase alphanumeric tag suitable for YAML/template keys."""
    return re_sub(r"[^a-z0-9]", "", value.lower())

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
            variables = safe_load(
                Path(env.variable_files[0]).read_text(encoding="utf-8")
            ) or {}
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
