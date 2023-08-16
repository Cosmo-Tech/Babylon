import click
import logging

from typing import Any
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")
env = Environment()


@click.command()
@timing_decorator
@pass_kusto_client
@inject_context_with_resource({'azure': ['resource_group_name'], 'adx': ['cluster_name', 'database_name']})
def get_all(
    context: Any,
    kusto_client: KustoManagementClient,
) -> CommandResponse:
    """
    List scripts on the database
    """
    resource_group_name = context['azure_resource_group_name']
    adx_cluster_name = context['adx_cluster_name']
    database_name = context['adx_database_name']
    response = kusto_client.scripts.list_by_database(resource_group_name=resource_group_name,
                                                     cluster_name=adx_cluster_name,
                                                     database_name=database_name)
    scripts = [item.as_dict() for item in response]
    return CommandResponse.success(scripts, verbose=True)
