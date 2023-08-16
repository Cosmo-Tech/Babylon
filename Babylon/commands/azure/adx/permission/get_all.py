import logging

from pprint import pformat
from typing import Any
from azure.mgmt.kusto import KustoManagementClient
from click import command
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_kusto_client
@inject_context_with_resource({'azure': ['resource_group_name'], 'adx': ['cluster_name', 'database_name']})
def get_all(context: Any, kusto_client: KustoManagementClient):
    """
    Get all permission assignments in the database
    """
    logger.info("Getting assignments...")
    resource_group_name = context['azure_resource_group_name']
    adx_cluster_name = context['adx_cluster_name']
    database_name = context['adx_database_name']
    assignments = kusto_client.database_principal_assignments.list(resource_group_name, adx_cluster_name, database_name)
    for ent in assignments:
        logger.info(f"{pformat(ent.__dict__)}")
    return CommandResponse.success({"assignments": assignments})
