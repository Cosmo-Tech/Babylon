import logging
from typing import Optional

from click import command
from click import option
from azure.mgmt.kusto import KustoManagementClient
import jmespath

from ....utils.decorators import require_deployment_key
from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")


@command()
@pass_kusto_client
@require_platform_key("resource_group_name", "resource_group_name")
@timing_decorator
@option("--filter", "filter", help="Filter response with a jmespath query")
def get_all(kusto_client: KustoManagementClient,
            resource_group_name: str,
            filter: Optional[str] = None) -> CommandResponse:
    """List scripts on the database"""
    response = kusto_client.clusters.list_by_resource_group(resource_group_name=resource_group_name)
    adx_clusters = [item.as_dict() for item in response]
    if filter:
        adx_clusters = jmespath.search(filter, adx_clusters)
    return CommandResponse.success(adx_clusters, verbose=True)
