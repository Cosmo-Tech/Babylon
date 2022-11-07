from typing import Optional
import json
import logging

from azure.mgmt.kusto import KustoManagementClient
from click import Context
from click import argument
from click import command
from click import pass_context
from click import Path
from click import option
from rich.pretty import Pretty

from ........utils.decorators import require_deployment_key
from ........utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("resource_group_name")
@require_platform_key("cluster_name")
@require_deployment_key("database_name")
@argument("principal_id")
@option(
    "-o",
    "--output-file",
    "output_file",
    type=Path(writable=True),
    help="The path to the file where ADT instances details should be outputted (json-formatted)",
)
def get(ctx: Context, resource_group_name: str, cluster_name: str, database_name: str, principal_id: str,
        output_file: Optional[str]):
    """Get permission assignments applied to the given principal id"""
    kusto_mgmt: KustoManagementClient = ctx.obj
    assignments = kusto_mgmt.database_principal_assignments.list(resource_group_name, cluster_name, database_name)
    entity_assignments = [assignment for assignment in assignments if assignment.principal_id == principal_id]
    if not entity_assignments:
        logger.info(f"No assignment found for principal ID {principal_id}")
        return
    logger.info(f"Found {len(entity_assignments)} assignments for principal ID {principal_id}")
    assigns = [assign.__dict__ for assign in assignments]
    if not output_file:
        logger.info(Pretty(assigns))
        return

    with open(output_file, "w") as _f:
        json.dump(assigns, _f, ensure_ascii=False)