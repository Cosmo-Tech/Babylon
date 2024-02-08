import logging
import jmespath

from click import option
from click import command
from typing import Any, Optional
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.decorators import retrieve_state, timing_decorator, wrapcontext

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@pass_kusto_client
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, kusto_client: KustoManagementClient, filter: Optional[str] = None) -> CommandResponse:
    """
    List scripts on the database
    """
    resource_group_name = state['azure_resource_group_name']
    response = kusto_client.clusters.list_by_resource_group(resource_group_name=resource_group_name)
    adx_clusters = [item.as_dict() for item in response]
    if filter:
        adx_clusters = jmespath.search(filter, adx_clusters)
    return CommandResponse.success(adx_clusters, verbose=True)
