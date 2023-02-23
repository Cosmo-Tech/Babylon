import logging

import click
from azure.mgmt.kusto import KustoManagementClient

from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse
from ......utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")


@click.command()
@pass_kusto_client
@require_platform_key("adx_cluster_name", "adx_cluster_name")
@require_platform_key("resource_group_name", "resource_group_name")
@require_deployment_key("adx_database_name", "adx_database_name")
@timing_decorator
def list_scripts(kusto_client: KustoManagementClient, adx_cluster_name: str, resource_group_name: str,
                 adx_database_name: str) -> CommandResponse:
    """List scripts on the database"""
    r = kusto_client.scripts.list_by_database(resource_group_name=resource_group_name,
                                              cluster_name=adx_cluster_name,
                                              database_name=adx_database_name)
    for script in r:
        logger.info(f"{script.name}")
    return CommandResponse.success({"scripts": r})
