"""
Superset helpers for dashboard deployment and embedded-UUID feedback.
"""

import uuid as _uuid_mod
from io import StringIO
from logging import getLogger
from pathlib import Path
from re import IGNORECASE, MULTILINE, compile, findall, sub
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

import requests
from requests.exceptions import RequestException
from ruamel.yaml import YAML as _RYAML
from yaml import safe_load

from Babylon.commands.macro.helpers.workspace.kubernetes_helper import get_postgres_service_host
from Babylon.utils.credentials import get_superset_token
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()

# Matches the top-level ``uuid`` field in a Superset export YAML.
_UUID_FIELD_RE = compile(
    r"^uuid:\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s*$",
    MULTILINE | IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public dispatch entry point
# ---------------------------------------------------------------------------


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
        pass  # return _deploy_powerbi(reports, state)
    logger.error("  [bold red]✘[/bold red] Unsupported dashboard provider '%s'", provider)
    return False, set()


# ---------------------------------------------------------------------------
# Superset deployment — top-level orchestration
# ---------------------------------------------------------------------------


def deploy_superset(
    reports: list,
    state: dict,
    superset_config: dict,
    deploy_dir: Path,
) -> tuple[bool, set[str]]:
    """Authenticate with Superset and deploy dashboard ZIPs sequentially.

    Returns:
        A tuple ``(success, zip_uuids)`` where *zip_uuids* is the union of all
        dashboard UUIDs from every processed ZIP — used by the caller to filter
        the embedded-UUID fetch to only the imported dashboards.
    """
    base_url = superset_config.get("superset_url", "").rstrip("/")
    if not base_url:
        logger.error("  [bold red]✘[/bold red] superset_url not configured")
        return False, set()

    valid_reports = [r for r in reports if isinstance(r, dict) and r.get("name") and r.get("path")]
    if not valid_reports:
        logger.warning("  [yellow]⚠[/yellow] No valid report entries each entry must have 'name' and 'path'")
        return True, set()

    superset_token = get_superset_token(base_url=base_url, config=superset_config)
    if not superset_token:
        logger.error("  [bold red]✘[/bold red] Failed to retrieve Superset token")
        return False, set()

    return deploy_superset_multiple_assets(
        superset_token=superset_token,
        reports=valid_reports,
        superset_config=superset_config,
        state=state,
        deploy_dir=deploy_dir,
    )


def deploy_superset_multiple_assets(
    superset_token: str,
    reports: list,
    state: dict,
    superset_config: dict,
    deploy_dir: Path,
) -> tuple[bool, set[str]]:
    """Deploy Superset dashboard assets from a list of ZIP reports.

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
        superset_token:  Superset JWT obtained from Keycloak exchange.
        reports:         List of dicts with 'name' and 'path' keys.
        state:           Full Babylon state dict.
        superset_config: Dict with at least 'superset_url'.
        deploy_dir:      Root deployment directory used to resolve report paths.

    Returns:
        A tuple ``(all_ok, all_zip_uuids)``.
    """
    base_url = superset_config.get("superset_url", "").rstrip("/")

    if not base_url:
        logger.error("  [bold red]✘[/bold red] superset_url not configured")
        return False, set()

    logger.info("  [dim]→ Deploying %d dashboard ZIP(s) to Superset...[/dim]", len(reports))

    csrf_token, db_uuid, sqlalchemy_uri = _setup_database_and_csrf(base_url, superset_token, superset_config)
    if not csrf_token or not sqlalchemy_uri:
        return False, set()

    workspace_id = state.get("services", {}).get("api", {}).get("workspace_id") or ""
    schema_name = workspace_id.replace("-", "_")

    all_ok = True
    all_zip_uuids: set[str] = set()
    abs_deploy_dir = Path(deploy_dir).resolve()

    force_new_uuids = _is_cross_workspace_deployment(
        reports=reports,
        abs_deploy_dir=abs_deploy_dir,
        base_url=base_url,
        superset_token=superset_token,
        schema_name=schema_name,
    )

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
            force_new_uuids=force_new_uuids,
        )
        if not success:
            all_ok = False
        all_zip_uuids |= new_uuids

    return all_ok, all_zip_uuids

def _setup_database_and_csrf(
    base_url: str,
    superset_token: str,
    superset_config: dict,
) -> tuple[str | None, str | None, str | None]:
    """Handle pre-flight checks: CSRF token, datasource creation, and DB URI building.

    Returns:
        ``(csrf_token, db_uuid, sqlalchemy_uri)`` or ``(None, None, None)`` on failure.
    """
    csrf_token = _get_superset_csrf_token(base_url, superset_token)
    if not csrf_token:
        logger.error("  [bold red]✘[/bold red] Could not obtain CSRF token.")
        return None, None, None

    datasource = create_postgres_datasource(superset_config=superset_config, superset_jwt=superset_token)
    if datasource is None:
        logger.error("  [bold red]✘[/bold red] Datasource creation failed Aborting")
        return None, None, None

    _ds_body = datasource.get("result") or datasource
    db_uuid: str = (_ds_body.get("uuid") or "").lower()

    if not db_uuid:
        logger.warning("  [yellow]⚠[/yellow] Datasource UUID not found UUID pinning will be skipped")

    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    if not api_config:
        logger.error("  [bold red]✘[/bold red] PostgreSQL API config secret not found")
        return None, None, None

    db_host = get_postgres_service_host(env.environ_id)
    sqlalchemy_uri = (
        f"postgresql+psycopg2://{api_config.get('reader-username')}:{api_config.get('reader-password')}"
        f"@{db_host}:5432/{api_config.get('database-name')}"
    )
    return csrf_token, db_uuid, sqlalchemy_uri


# ---------------------------------------------------------------------------
# Datasource management
# ---------------------------------------------------------------------------


def create_postgres_datasource(
    superset_config: dict,
    superset_jwt: str | None = None,
) -> dict | None:
    """Create a new PostgreSQL database connection in Superset (idempotent).

    Returns:
        The datasource dict on success or if it already exists, ``None`` on error.
    """
    base_url = (superset_config.get("superset_url") or "").rstrip("/")
    if not base_url:
        logger.error("  [bold red]✘[/bold red] superset_url not configured")
        return None

    if not superset_jwt:
        superset_jwt = get_superset_token(base_url=base_url, config=superset_config)
        if not superset_jwt:
            logger.error("  [bold red]✘[/bold red] Could not obtain Superset JWT for datasource creation")
            return None

    csrf_token = _get_superset_csrf_token(base_url, superset_jwt)
    if not csrf_token:
        logger.error("  [bold red]✘[/bold red] Could not obtain CSRF token for datasource creation")
        return None

    display_name = env.environ_id
    existing = _get_existing_datasource(base_url, superset_jwt, display_name)
    if existing:
        logger.info("  [yellow]⚠[/yellow] [dim]Datasource '%s' already configured (id=%s)[/dim]", display_name, existing.get("id"))
        return existing

    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
    db_name = api_config.get("database-name")
    sqlalchemy_uri = (
        f"postgresql+psycopg2://{api_config.get('writer-username')}:{api_config.get('writer-password')}"
        f"@{get_postgres_service_host(env.environ_id)}:5432/{db_name}"
    )

    headers = {
        "Authorization": f"Bearer {superset_jwt}",
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token,
        "Referer": base_url,
    }
    payload = {
        "database_name": display_name,
        "sqlalchemy_uri": sqlalchemy_uri,
        "expose_in_sqllab": True,
        "allow_run_async": False,
    }

    try:
        response = requests.post(f"{base_url}/api/v1/database/", headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        logger.info("  [bold green]✔[/bold green] Datasource '%s' created", display_name)
        return response.json()
    except Exception as exp:
        logger.error("  [bold red]✘[/bold red] Failed to create datasource '%s': %s", display_name, exp)
        return None


def _get_existing_datasource(base_url: str, superset_jwt: str, display_name: str) -> dict | None:
    """Return the existing Superset database entry matching *display_name*, or None."""
    headers = {"Authorization": f"Bearer {superset_jwt}"}
    try:
        response = requests.get(f"{base_url}/api/v1/database/", headers=headers, timeout=10)
        response.raise_for_status()
        for db in response.json().get("result", []):
            if db.get("database_name") == display_name:
                return db
    except Exception as exp:
        logger.debug(f"  Could not list Superset databases: {exp}")
    return None


# ---------------------------------------------------------------------------
# Cross-workspace pre-check
# ---------------------------------------------------------------------------


def _is_cross_workspace_deployment(
    reports: list,
    abs_deploy_dir: Path,
    base_url: str,
    superset_token: str,
    schema_name: str,
) -> bool:
    """Determine whether this batch of ZIPs targets a different workspace.

    Must be called **before** any ZIP is imported so that Superset state is
    still clean (no datasets from the current batch exist yet).

    Logic:
    1. Collect chart/dashboard UUIDs from ALL ZIPs.
    2. Check if any of them already exist in Superset.
    3. If yes: check whether datasets in the target schema exist.
       - Yes → same workspace redeploy → return False.
       - No  → cross-workspace → return True.
    4. If no UUIDs match → first deploy → return False.

    Returns:
        ``True`` when all ZIPs should regenerate UUIDs (cross-workspace).
    """
    if not schema_name:
        return False

    # Collect all UUIDs from every ZIP in the batch.
    all_uuids: set[str] = set()
    for report in reports:
        rel_path = report.get("path", "")
        path_obj = Path(rel_path)
        zip_path = path_obj.resolve() if path_obj.is_absolute() else (abs_deploy_dir / rel_path).resolve()
        if zip_path.exists():
            all_uuids |= _read_uuids_from_zip(zip_path)

    if not all_uuids:
        return False

    headers = {"Authorization": f"Bearer {superset_token}"}

    # Check if any chart/dashboard UUID already exists in Superset.
    any_matched = False
    for endpoint in ("/api/v1/chart/", "/api/v1/dashboard/"):
        try:
            resp = requests.get(
                f"{base_url}{endpoint}",
                headers=headers,
                params={"page_size": 1000},
                timeout=10,
            )
            resp.raise_for_status()
            existing = {(item.get("uuid") or "").lower() for item in resp.json().get("result", [])}
            if all_uuids & existing:
                any_matched = True
                break
        except Exception:
            pass

    if not any_matched:
        return False

    # Chart/dashboard UUIDs exist → check if datasets in the target schema exist.
    try:
        resp = requests.get(
            f"{base_url}/api/v1/dataset/",
            headers=headers,
            params={"page_size": 1000},
            timeout=10,
        )
        resp.raise_for_status()
        has_target_schema = any(
            (d.get("schema") or "").strip() == schema_name
            for d in resp.json().get("result", [])
        )
    except Exception:
        has_target_schema = False

    if has_target_schema:
        return False

    logger.info(
        "  [bold yellow]⚠[/bold yellow] [dim]Cross-workspace deployment detected: New Schema '%s'. Forcing UUID regeneration.[/dim]",
        schema_name,
    )
    return True


# ---------------------------------------------------------------------------
# Per-ZIP processing
# ---------------------------------------------------------------------------


def _process_dashboard_zip(
    report: dict,
    abs_deploy_dir: Path,
    base_url: str,
    superset_token: str,
    csrf_token: str,
    sqlalchemy_uri: str,
    db_uuid: str,
    schema_name: str,
    force_new_uuids: bool = False,
) -> tuple[bool, set[str]]:
    """Extract, patch, repack, and import a single dashboard ZIP.

    Args:
        force_new_uuids: When ``True``, skip the Superset existence check and
                         regenerate all UUIDs unconditionally (cross-workspace).

    Returns:
        ``(success, new_dashboard_uuids)`` where *new_dashboard_uuids* are the
        post-regen UUIDs collected from ``dashboards/`` after patching.
    """
    name: str = report.get("name", "")
    rel_path: str = report.get("path", "")
    path_obj = Path(rel_path)
    zip_path = path_obj.resolve() if path_obj.is_absolute() else (abs_deploy_dir / rel_path).resolve()

    if not zip_path.exists():
        logger.error("  [bold red]✘[/bold red] ZIP not found: %s", zip_path)
        return False, set()

    zip_uuids = _read_uuids_from_zip(zip_path)

    if force_new_uuids:
        existing_map = {"datasets": False, "charts": False, "dashboards": False}
    else:
        existing_map = _assets_exist_in_superset(base_url, superset_token, zip_uuids, schema_name=schema_name)

    is_update = any(existing_map.values())
    if is_update:
        updating = [k for k, v in existing_map.items() if v]
        logger.info(
            f"  [yellow]⚠[/yellow] [dim]Dashboard [magenta]{name}[/magenta] "
            f"already deployed updating: '{', '.join(updating)}'[/dim]"
        )
    else:
        logger.info("  [dim]→ Dashboard [magenta]%s[/magenta] first deployment, creating all assets[/dim]", name)
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
                        logger.warning(f"  [yellow]⚠[/yellow] Skipping unreadable YAML file '{df.name}'")
                        logger.debug(f"  Could not read YAML file '{df.name}': {e}")
                        
            _repack_zip(zip_path, tmp_dir)

    except (OSError, BadZipFile) as exc:
        logger.error("  [bold red]✘[/bold red] ZIP processing error for '%s': %s", zip_path.name, exc)
        return False, set()

    if not _import_zip_to_superset(base_url, superset_token, csrf_token, zip_path):
        return False, set()

    return True, new_dashboard_uuids


# ---------------------------------------------------------------------------
# ZIP inspection and UUID management
# ---------------------------------------------------------------------------


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
        logger.error(f"  [bold red]✘[/bold red] Could not read UUIDs from {zip_path.name}: {exc}")
    return uuids


def _assets_exist_in_superset(
    base_url: str,
    superset_jwt: str,
    uuids: set[str],
    schema_name: str = "",
) -> dict[str, bool]:
    """Check which asset types from the export ZIP already exist in Superset.

    Cross-workspace detection is handled upfront by
    ``_is_cross_workspace_deployment`` — this function is only called when
    we already know we are in a same-workspace context.

    **Dataset detection:**
    The dataset list endpoint does NOT return ``uuid``, so datasets are
    inferred as existing when charts or dashboards from this ZIP match
    (proving this specific dashboard was deployed before for this workspace).
    """
    result: dict[str, bool] = {"datasets": False, "charts": False, "dashboards": False}
    if not uuids:
        return result

    headers = {"Authorization": f"Bearer {superset_jwt}"}

    _checks: list[tuple[str, str, str]] = [
        ("charts", "/api/v1/chart/", "uuid"),
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
            existing = {(item.get(uuid_field) or "").lower() for item in response.json().get("result", [])}
            if uuids & existing:
                result[folder_key] = True
        except Exception as exc:
            logger.error(f"  [bold red]✘[/bold red] Could not query Superset {folder_key}: {exc}")

    if result["charts"] or result["dashboards"]:
        result["datasets"] = True

    return result


def _regenerate_superset_uuids(
    base_dir_path: str | Path,
    existing: dict[str, bool] | None = None,
) -> dict:
    """Regenerate UUIDs for Superset components that haven't been deployed yet.

    Skips ``databases/`` and any folder marked as deployed in *existing*.
    Pass 1 collects old→new UUID mapping; Pass 2 replaces across all files
    so cross-references (e.g. chart → dataset_uuid) remain consistent.

    Returns:
        ``{old_uuid: new_uuid}`` mapping, empty if nothing was regenerated.
    """
    base_dir = Path(base_dir_path)
    existing = existing or {}

    skip_folders = {"databases"} | {folder for folder, deployed in existing.items() if deployed}
    active = sorted({"datasets", "charts", "dashboards", "themes"} - skip_folders)

    all_files: list[Path] = sorted(base_dir.rglob("*.yaml"))
    uuid_mapping: dict[str, str] = {}

    for yaml_file in all_files:
        try:
            top_folder = yaml_file.relative_to(base_dir).parts[0]
        except (ValueError, IndexError):
            top_folder = ""

        if top_folder in skip_folders:
            continue
        try:
            raw = yaml_file.read_text(encoding="utf-8")
            match = _UUID_FIELD_RE.search(raw)
            if match:
                old_uuid = match.group(1).lower()
                uuid_mapping[old_uuid] = str(_uuid_mod.uuid4())
        except (OSError, UnicodeError) as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not read {yaml_file.name} for UUID extraction: {exc}")

    if not uuid_mapping:
        return {}

    for yaml_file in all_files:
        try:
            raw = yaml_file.read_text(encoding="utf-8")
            patched = raw
            for old_uuid, new_uuid in uuid_mapping.items():
                patched = patched.replace(old_uuid, new_uuid)
                patched = patched.replace(old_uuid.upper(), new_uuid)
            if patched != raw:
                yaml_file.write_text(patched, encoding="utf-8", newline="\n")
        except (OSError, UnicodeError) as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not update UUIDs in {yaml_file.name}: {exc}")

    logger.debug("  Regenerated %d UUID(s) for [%s]", len(uuid_mapping), ", ".join(active))
    return uuid_mapping


# ---------------------------------------------------------------------------
# ZIP content patching helpers
# ---------------------------------------------------------------------------


def _patch_metadata(content_dir: Path) -> None:
    """Ensure metadata.yaml declares ``type: assets`` for the assets import endpoint."""
    meta_file = content_dir / "metadata.yaml"
    if not meta_file.is_file():
        return
    try:
        raw = meta_file.read_text(encoding="utf-8")
        patched = sub(pattern=r"^(type:\s*).*$", repl=r"\g<1>assets", string=raw, flags=MULTILINE)
        if patched != raw:
            meta_file.write_text(patched, encoding="utf-8", newline="\n")
    except OSError as exp:
        logger.error(f"  [bold red]✘[/bold red] File system error while patching 'metadata.yaml': {exp}")


def _patch_database_dir(tmp_dir: Path, sqlalchemy_uri: str, database_name: str, db_uuid: str = "") -> None:
    """Patch ``sqlalchemy_uri``, ``database_name``, and optionally ``uuid`` in ``databases/``.

    Args:
        tmp_dir:        Root of the unzipped export.
        sqlalchemy_uri: Full SQLAlchemy connection string for the target env.
        database_name:  Superset display name for the database (``env.environ_id``).
        db_uuid:        UUID returned by Superset after datasource creation.
                        Pass an empty string to skip UUID pinning.
    """
    db_dir = tmp_dir / "databases"
    if not db_dir.is_dir():
        return

    _uri_re = compile(r"^(sqlalchemy_uri:\s*).*$", MULTILINE)
    _name_re = compile(r"^(database_name:\s*).*$", MULTILINE)
    _uuid_re = compile(r"^(uuid:\s*)([0-9a-f-]{36})\s*$", MULTILINE | IGNORECASE)

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
                yaml_file.write_text(result, encoding="utf-8", newline="\n")
        except Exception as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not patch databases/{yaml_file.name}: {exc}")


def _patch_schema_in_datasets_dir(tmp_dir: Path, schema_name: str, db_uuid: str = "") -> None:
    """Patch schema references and optionally pin ``database_uuid`` in every dataset YAML.

    Args:
        tmp_dir:     Root of the unzipped export.
        schema_name: Target PostgreSQL schema for the current workspace.
        db_uuid:     Superset database UUID.  Pass an empty string to skip pinning.
    """
    datasets_dir = tmp_dir / "datasets"
    if not datasets_dir.is_dir():
        return

    _schema_re = compile(r"^(schema:\s*)(\S+)\s*$", MULTILINE)
    _db_uuid_re = compile(r"^(database_uuid:\s*)([0-9a-f-]{36})\s*$", MULTILINE | IGNORECASE)

    for yaml_file in datasets_dir.rglob("*.yaml"):
        try:
            raw = yaml_file.read_text(encoding="utf-8")
            result = raw

            match = _schema_re.search(result)
            if match:
                old_schema = match.group(2)
                if old_schema != schema_name:
                    result = result.replace(old_schema, schema_name)

            if db_uuid and "database_uuid" in result:
                new_result = _db_uuid_re.sub(rf"\g<1>{db_uuid}", result)
                if new_result != result:
                    result = new_result

            if result != raw:
                yaml_file.write_text(result, encoding="utf-8", newline="\n")
        except Exception as exc:
            logger.warning(f"  [yellow]⚠[/yellow] Could not patch dataset {yaml_file.name}: {exc}")


def _repack_zip(zip_path: Path, tmp_dir: Path) -> None:
    """Repack the contents of *tmp_dir* back into *zip_path*, replacing it in-place."""
    root_name = zip_path.stem
    tmp_items = list(tmp_dir.iterdir())
    base = tmp_items[0] if len(tmp_items) == 1 and tmp_items[0].is_dir() else tmp_dir

    try:
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
            for file in sorted(base.rglob("*")):
                if file.is_file():
                    arcname = f"{root_name}/{file.relative_to(base).as_posix()}"
                    zf.write(file, arcname)
        logger.debug("  Repacked '%s'", zip_path.name)
    except OSError as exp:
        logger.error(f"  [bold red]✘[/bold red] Error repacking '{zip_path.name}': {exp}")
        raise


# ---------------------------------------------------------------------------
# Superset import
# ---------------------------------------------------------------------------


def _import_zip_to_superset(
    base_url: str,
    superset_jwt: str,
    csrf_token: str,
    zip_path: Path,
) -> bool:
    """POST a zip bundle to the Superset API to import all assets at once.

    Returns:
        True on successful import (HTTP 2xx), False on any error.
    """
    url = f"{base_url}/api/v1/assets/import/"
    headers = {
        "Authorization": f"Bearer {superset_jwt}",
        "X-CSRFToken": csrf_token,
        "Referer": base_url,
    }
    try:
        with zip_path.open("rb") as fh:
            files = {"bundle": (zip_path.name, fh, "application/zip")}
            response = requests.post(url, headers=headers, files=files, data={"overwrite": "true"}, timeout=60)
        response.raise_for_status()
        logger.info(f"  [bold green]✔[/bold green] Zip [cyan]{zip_path.name}[/cyan] imported into Superset")
        return True
    except RequestException as exp:
        logger.error(f"  [bold red]✘[/bold red] Failed to import '{zip_path.name}': {exp}")
        return False
    except Exception as exp:
        logger.error(f"  [bold red]✘[/bold red] Unexpected error importing '{zip_path.name}': {exp}")
        return False


# ---------------------------------------------------------------------------
# CSRF helper
# ---------------------------------------------------------------------------


def _get_superset_csrf_token(base_url: str, bearer_token: str) -> str | None:
    """Fetch a CSRF token from Superset (required for all write operations).

    Returns:
        The CSRF token string, or ``None`` on failure.
    """
    url = f"{base_url.rstrip('/')}/api/v1/security/csrf_token/"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {bearer_token}"}, timeout=10)
        response.raise_for_status()
        csrf = response.json().get("result")
        if not csrf:
            logger.error("  [bold red]✘[/bold red] CSRF token not found in Superset response")
        return csrf
    except Exception as exp:
        logger.error(f"  [bold red]✘[/bold red] Failed to fetch Superset CSRF token: {exp}")
        return None


# ---------------------------------------------------------------------------
# Embedded-UUID feedback pipeline
# ---------------------------------------------------------------------------


def _fetch_and_store_embedded_dashboard_uuids(
    base_url: str,
    superset_jwt: str,
    zip_uuids: set[str] | None = None,
) -> bool:
    """Enable embedding and fetch the embedded UUID for each imported dashboard,
    then persist them into the Babylon variables file.

    YAML structure written per dashboard::

        expertview:
          uuid: "abc-embedded-token-uuid"
          original_id: "42"

    Args:
        base_url:     Superset base URL.
        superset_jwt: Valid Superset Bearer token.
        zip_uuids:    Set of dashboard UUIDs from the imported ZIP.  When
                      provided, only dashboards matching this set are processed.

    Returns:
        True if at least one embedded UUID was written; False on total failure.
    """
    if not env.variable_files:
        logger.warning("  [yellow]⚠[/yellow] No variable files configured cannot persist embedded UUIDs")
        return False

    variables_yaml_path = Path(env.variable_files[0])
    auth_headers = {"Authorization": f"Bearer {superset_jwt}"}

    dashboards = _get_filtered_dashboards(base_url, auth_headers, zip_uuids)
    if dashboards is None:
        return False
    if not dashboards:
        logger.warning("  [yellow]⚠[/yellow] No imported dashboards found skipping")
        return False

    updates: dict[str, dict] = {}
    for dashboard in dashboards:
        result = _get_embedded_uuid_for_dashboard(base_url, superset_jwt, auth_headers, dashboard)
        if result is None:
            continue
        key, embedded_uuid, original_id = result
        updates[key] = {"uuid": embedded_uuid, "original_id": original_id}

    if not updates:
        logger.warning("  [yellow]⚠[/yellow] No embedded UUIDs retrieved variables file not updated")
        return False

    if not _write_dashboard_updates_to_yaml(variables_yaml_path, updates):
        return False

    logger.info(
        f"  [bold green]✔[/bold green] Variable file "
        f"[dim]'{variables_yaml_path.name}'[/dim] updated with "
        f"{len(updates)} embedded dashboard UUID(s)"
    )
    return True


def _get_filtered_dashboards(
    base_url: str,
    headers: dict,
    zip_uuids: set[str] | None,
) -> list[dict] | None:
    """Fetch all Superset dashboards and filter to those present in *zip_uuids*.

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
    return filtered


def _get_embedded_uuid_for_dashboard(
    base_url: str,
    superset_jwt: str,
    auth_headers: dict,
    dashboard: dict,
) -> tuple[str, str, str] | None:
    """Enable embedding for one dashboard and return ``(key, uuid, original_id)``.

    Returns ``None`` when the dashboard should be skipped.
    """
    name: str = (dashboard.get("dashboard_title") or dashboard.get("slug") or "").strip()
    dash_uuid: str = (dashboard.get("uuid") or "").lower()
    integer_id: int | None = dashboard.get("id")

    if not dash_uuid or not name or not integer_id:
        logger.warning(f"  [yellow]⚠[/yellow] Skipping dashboard missing required field(s) (name, uuid, or id): {dashboard}")
        return None

    key = sub(r"[^a-z0-9]", "", name.lower())
    if not key:
        logger.warning(f"  [yellow]⚠[/yellow] Dashboard '{name}' produced an empty sanitised key skipping")
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
    except Exception:
        logger.error(f"  [bold red]✘[/bold red] Could not fetch embedded UUID for dashboard '{name}' (id={integer_id})")
        return None

    result_block: dict = emb_resp.json().get("result") or {}
    embedded_uuid: str = (result_block.get("uuid") or "").strip()
    if not embedded_uuid:
        logger.warning(f"  [yellow]⚠[/yellow] Dashboard '{name}' (id={integer_id}) returned no embedded UUID")
        return None

    original_id = str(result_block.get("dashboard_id") or integer_id)
    logger.info(f"  [bold green]✔[/bold green] Embedding enabled for dashboard '{name}' (key='{key}')")
    return key, embedded_uuid, original_id


def _enable_dashboard_embedding(
    base_url: str,
    superset_jwt: str,
    auth_headers: dict,
    integer_id: int,
    name: str,
) -> bool:
    """Enable embedding on a single Superset dashboard via POST (idempotent).

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
        logger.error(f"  [bold red]✘[/bold red] Could not enable embedding for '{name}' (id={integer_id})")
        return False
    return True


# ---------------------------------------------------------------------------
# Variables YAML persistence
# ---------------------------------------------------------------------------


def _write_dashboard_updates_to_yaml(
    variables_yaml_path: Path,
    updates: dict[str, dict],
) -> bool:
    """Persist ``{key: {uuid, original_id}}`` mapping into the variables YAML.

    Returns:
        ``True`` if at least one entry was written, ``False`` otherwise.
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
            logger.warning(f"  [yellow]⚠[/yellow] Failed to write entry '{key}' to '{variables_yaml_path.name}'")
            continue
        any_written = True
    return any_written


def update_variables_file_entry(
    variables_path: Path,
    key: str,
    uuid: str,
    original_id: str | None = None,
) -> bool:
    """Update a single dashboard entry in a Babylon variables YAML file in-place.

    Uses ``ruamel.yaml`` to preserve all existing formatting, comments, and
    template variables verbatim. Only the target ``key`` block is touched.

    Args:
        variables_path: Absolute path to the Babylon ``variables.yaml`` file.
                        Must **not** be a ``.tpl`` template file.
        key:            Sanitised dashboard name used as the YAML key.
        uuid:           New embedded dashboard UUID to write.
        original_id:    Superset integer dashboard ID (as string).

    Returns:
        ``True`` on success, ``False`` on any error.
    """
    if not variables_path.is_file():
        logger.error(f"  [bold red]✘[/bold red] Variables file not found: {variables_path}")
        return False
    if variables_path.suffix in {".tpl", ".tmpl", ".template"}:
        logger.error(f"  [bold red]✘[/bold red] Refusing to modify a template file: {variables_path}")
        return False

    try:
        ry = _RYAML()
        ry.preserve_quotes = True
        ry.width = 4096
        ry.best_map_flow_style = False

        raw = variables_path.read_text(encoding="utf-8")
        data = ry.load(raw)
        if data is None:
            data = ry.load("{}")

        entry = data.get(key)
        if isinstance(entry, dict):
            entry["uuid"] = uuid
            if original_id is not None:
                entry["original_id"] = str(original_id)
        else:
            new_entry: dict = {"uuid": uuid}
            if original_id is not None:
                new_entry["original_id"] = str(original_id)
            data[key] = new_entry

        buf = StringIO()
        ry.dump(data, buf)
        variables_path.write_text(buf.getvalue(), encoding="utf-8", newline="\n")
        return True
    except OSError as exc:
        logger.error(f"  [bold red]✘[/bold red] File system error updating '{variables_path.name}': {exc}")
    except Exception as exc:
        logger.error(f"  [bold red]✘[/bold red] YAML error updating '{variables_path.name}': {exc}")
    return False


# ---------------------------------------------------------------------------
# Template rendering helpers (used by deploy_workspace.py)
# ---------------------------------------------------------------------------


def _build_dashboard_ext_args(fallback_empty: bool = False, template_content: str = "") -> dict:
    """Extract embedded dashboard UUIDs from the Babylon variables file.

    Args:
        fallback_empty:   When ``True``, missing UUIDs and unresolved template
                          variables are mapped to ``""`` (safe phase-1 render).
        template_content: Raw Workspace template string, used to discover
                          missing variables when *fallback_empty* is True.

    Returns:
        ``{key: uuid_string}`` dict ready for ``ext_args``.
    """
    if not env.variable_files:
        return {}
    try:
        raw = Path(env.variable_files[0]).read_text(encoding="utf-8")
        variables: dict = safe_load(raw) or {}
    except OSError:
        return {}

    ext: dict = {}
    for key, value in variables.items():
        if not isinstance(value, dict):
            continue
        if "uuid" not in value or "original_id" not in value:
            continue
        uuid = get_dashboard_embedded_uuid(variables, key)
        if uuid:
            ext[key] = uuid
        elif fallback_empty:
            ext[key] = ""

    if fallback_empty and template_content:
        known = variables.keys() | ext.keys()
        for var in findall(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}", template_content):
            if var not in known:
                ext[var] = ""

    return ext


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


def get_dashboard_embedded_uuid(yaml_data: dict, sanitised_key: str) -> str | None:
    """Safely retrieve the embedded UUID for a dashboard from loaded YAML data.

    Accepts both the current dict format ``{uuid: ..., original_id: ...}`` and
    a legacy flat string value.

    Returns:
        The embedded UUID string, or ``None`` if absent.
    """
    if not yaml_data or not sanitised_key:
        return None

    entry = yaml_data.get(sanitised_key)
    if entry is None:
        logger.warning(f"  [yellow]⚠[/yellow] Dashboard key '{sanitised_key}' not found in variables file")
        return None
    if isinstance(entry, str):
        return entry or None
    if isinstance(entry, dict):
        uuid = entry.get("uuid")
        if not uuid:
            logger.warning(f"  [yellow]⚠[/yellow] Dashboard '{sanitised_key}' found in variables but 'uuid' field is empty")
        return uuid or None

    logger.warning(
            f"  [yellow]⚠[/yellow] Unexpected value type for dashboard key "
            f"'{sanitised_key}': expected str or dict, got {type(entry).__name__}"
        )
    return None


def get_uuid_by_dashboard_id(yaml_data: dict, target_id: str | int) -> str | None:
    """Reverse-lookup the embedded UUID by Superset integer dashboard ID.

    More reliable than reconstructing the sanitised key from a name because
    the integer ID is stable across renames.

    Returns:
        The embedded UUID string if found, ``None`` otherwise.
    """
    if not yaml_data:
        return None

    target = str(target_id)
    for key, entry in yaml_data.items():
        if not isinstance(entry, dict):
            continue
        if str(entry.get("original_id") or "") == target:
            uuid = entry.get("uuid")
            return uuid or None

    logger.warning(f"  [yellow]⚠[/yellow] No dashboard entry with original_id='{target}' found in variables")
    return None
