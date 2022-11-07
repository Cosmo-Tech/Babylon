import logging
import pathlib
import json

from azure.mgmt.kusto import KustoManagementClient
from click import Context
from click import command
from click import pass_context
from click import option
from click import Path
from rich import print

from ........utils.decorators import require_deployment_key
from ........utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("resource_group_name")
@require_platform_key("cluster_name")
@require_deployment_key("database_name")
@option(
    "-o",
    "--output-file",
    "output_file",
    type=Path(writable=True),
    help="The path to the file where ADT instances details should be outputted (json-formatted)",
)
def get_all(ctx: Context, resource_group_name: str, cluster_name: str, database_name: str, output_file: pathlib.Path):
    """Get all permission assignments in the database"""
    kusto_mgmt: KustoManagementClient = ctx.obj
    logger.info("Getting assignments...")
    assignments = kusto_mgmt.database_principal_assignments.list(resource_group_name, cluster_name, database_name)
    assigns = [assign.__dict__ for assign in assignments]
    if not output_file:
        print(assigns)
        return

    with open(output_file, "w") as _f:
        json.dump(assigns, _f, ensure_ascii=False)
