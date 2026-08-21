"""
Workspace helpers package.

Re-exports every public symbol that was previously available via the
monolithic ``helpers/workspace.py`` module, preserving full backward
compatibility for all existing importers (``destroy.py``,
``deploy_workspace.py``, etc.).
"""

from Babylon.commands.macro.helpers.workspace.api_cosmotech_helper import (
    create_workspace,
    delete_api_resource,
    sync_workspace_security,
    update_workspace,
)
from Babylon.commands.macro.helpers.workspace.kubernetes_helper import (
    create_coal_configmap,
    create_workspace_secret,
    delete_kubernetes_resources,
    deploy_postgres_schema,
    destroy_postgres_schema,
    get_postgres_service_host,
)
from Babylon.commands.macro.helpers.workspace.superset_helper import (
    _build_dashboard_ext_args,
    _fetch_and_store_embedded_dashboard_uuids,
    create_postgres_datasource,
    delete_superset_assets,
    deploy_dashboard,
    deploy_superset,
    deploy_superset_multiple_assets,
    destroy_dashboard_assets,
    get_dashboard_embedded_uuid,
    get_uuid_by_dashboard_id,
    update_variables_file_entry,
)
from Babylon.commands.macro.helpers.workspace.powerbi_helper import build_powerbi_ext_args, deploy_powerbi, destroy_powerbi_assets

__all__ = [
    # api_cosmotech_helper
    "create_workspace",
    "update_workspace",
    "delete_api_resource",
    "sync_workspace_security",
    # kubernetes_helper
    "deploy_postgres_schema",
    "destroy_postgres_schema",
    "delete_kubernetes_resources",
    "get_postgres_service_host",
    "create_workspace_secret",
    "create_coal_configmap",
    # superset_helper
    "deploy_dashboard",
    "deploy_superset",
    "deploy_superset_multiple_assets",
    "destroy_dashboard_assets",
    "create_postgres_datasource",
    "delete_superset_assets",
    "_fetch_and_store_embedded_dashboard_uuids",
    "_build_dashboard_ext_args",
    "get_dashboard_embedded_uuid",
    "get_uuid_by_dashboard_id",
    "update_variables_file_entry",
    # powerbi_helper
    "deploy_powerbi",
    "destroy_powerbi_assets",
    "build_powerbi_ext_args",
]
