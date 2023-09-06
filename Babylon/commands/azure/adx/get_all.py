import logging
from typing import Any, Optional

from click import command
from click import option
from azure.mgmt.kusto import KustoManagementClient
import jmespath

from Babylon.utils.decorators import inject_context_with_resource, timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@pass_kusto_client
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({'azure': ['resource_group_name']})
def get_all(context: Any, kusto_client: KustoManagementClient, filter: Optional[str] = None) -> CommandResponse:
    """
    List scripts on the database
    """
    resource_group_name = context['azure_resource_group_name']
    response = kusto_client.clusters.list_by_resource_group(resource_group_name=resource_group_name)
    adx_clusters = [item.as_dict() for item in response]
    if filter:
        adx_clusters = jmespath.search(filter, adx_clusters)
    return CommandResponse.success(adx_clusters, verbose=True)
