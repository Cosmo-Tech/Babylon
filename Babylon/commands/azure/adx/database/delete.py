import logging

from typing import Any, Optional
from click import argument, command, option
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.typing import QueryType
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@pass_kusto_client
@option("--current", "current", type=QueryType(), is_flag=True, help="Delete database adx referenced in configuration")
@argument("name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name'], 'adx': ['cluster_name', 'database_name']})
def delete(context: Any,
           kusto_client: KustoManagementClient,
           name: Optional[str] = None,
           current: bool = False) -> CommandResponse:
    """
    Delete database in ADX cluster
    """
    resource_group_name = context['azure_resource_group_name']
    adx_cluster_name = context['adx_cluster_name']
    database_name = context["adx_database_name"] if current else name
    try:
        kusto_client.databases.get(
            resource_group_name=resource_group_name,
            cluster_name=adx_cluster_name,
            database_name=database_name,
        )
    except Exception as ex:
        logger.error(ex)
        return CommandResponse.fail()

    poller = kusto_client.databases.begin_delete(
        resource_group_name=resource_group_name,
        cluster_name=adx_cluster_name,
        database_name=database_name,
    )
    poller.wait()
    if not poller.done():
        return CommandResponse.fail()
    if poller.status() == "Succeeded":
        _ret: list[str] = ["Provisioning state: Deleted"]
    logger.info("\n".join(_ret))
    return CommandResponse.success()
