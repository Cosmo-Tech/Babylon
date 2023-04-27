import logging
from typing import Optional

from click import argument, command, option
from azure.mgmt.kusto import KustoManagementClient

from Babylon.utils.typing import QueryType
from .....utils.clients import pass_kusto_client

from .....utils.response import CommandResponse
from .....utils.environment import Environment
from .....utils.decorators import require_deployment_key
from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_kusto_client
@require_deployment_key("resource_group_name")
@require_platform_key('adx_cluster_name')
@timing_decorator
@option("--current", "current", type=QueryType(), is_flag=True, help="Delete database adx referenced in configuration")
@argument("database_name", type=QueryType(), default="%deploy%adx_database_name")
def delete(kusto_client: KustoManagementClient,
           resource_group_name: str,
           adx_cluster_name: str,
           database_name: Optional[str] = None,
           current: bool = False) -> CommandResponse:
    """Delete database in ADX cluster"""

    if current:
        env = Environment()
        database_name = env.configuration.get_deploy_var("adx_database_name")

    try:
        kusto_client.databases.get(
            resource_group_name=resource_group_name,
            cluster_name=adx_cluster_name,
            database_name=database_name,
        )
    except Exception as ex:
        logger.error(ex)
        return CommandResponse.fail()

    try:
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
    except Exception as ex:
        logger.info(ex)
        return CommandResponse.fail()
