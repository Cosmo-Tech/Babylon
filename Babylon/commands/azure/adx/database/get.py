import logging
from typing import Optional

from click import argument, command
from azure.mgmt.kusto import KustoManagementClient
from .....utils.clients import pass_kusto_client

from .....utils.response import CommandResponse
from .....utils.decorators import require_deployment_key
from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_kusto_client
@require_deployment_key("resource_group_name")
@require_platform_key('adx_cluster_name')
@timing_decorator
@argument("database_name")
def get(kusto_client: KustoManagementClient,
        resource_group_name: str,
        adx_cluster_name: str,
        database_name: Optional[str] = None) -> CommandResponse:
    """Retrieve database from ADX cluster given"""

    try:
        database = kusto_client.databases.get(resource_group_name=resource_group_name,
                                              cluster_name=adx_cluster_name,
                                              database_name=database_name)
        _ret: list[str] = []
        for k, v in database.as_dict().items():
            _ret.append(f"{k}:{v}")
        logger.info("\n".join(_ret))
        return CommandResponse.success()
    except Exception as ex:
        logger.info(ex)
        return CommandResponse.fail()
