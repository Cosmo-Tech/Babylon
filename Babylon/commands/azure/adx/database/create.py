import logging
from typing import Optional

from click import argument, command, option
from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.kusto.models import ReadWriteDatabase
from azure.mgmt.kusto.models import CheckNameRequest

from Babylon.utils.typing import QueryType

from .....utils.clients import pass_kusto_client
from .....utils.environment import Environment
from .....utils.response import CommandResponse
from .....utils.decorators import require_deployment_key
from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator

from datetime import timedelta

logger = logging.getLogger("Babylon")


@command()
@pass_kusto_client
@require_deployment_key("resource_group_name")
@require_deployment_key('resources_location')
@require_platform_key('adx_cluster_name')
@timing_decorator
@option(
    "-s",
    "--select",
    "select",
    is_flag=True,
    help="Select this new database in configuration ?",
)
@argument("database_name", type=QueryType(), default="%deploy%adx_database_name")
def create(kusto_client: KustoManagementClient,
           resource_group_name: str,
           resources_location: str,
           adx_cluster_name: str,
           database_name: Optional[str] = None,
           select: bool = False) -> CommandResponse:
    """Create database in ADX cluster"""

    # parameters
    # soft delete period by default 365 days
    # cache period by default 31 days
    params_database = ReadWriteDatabase(location=resources_location,
                                        soft_delete_period=timedelta(days=365),
                                        hot_cache_period=timedelta(days=31))

    try:
        name_request = CheckNameRequest(name=database_name, type="Microsoft.Kusto/clusters/databases")
        name_result = kusto_client.databases.check_name_availability(resource_group_name=resource_group_name,
                                                                     cluster_name=adx_cluster_name,
                                                                     resource_name=name_request,
                                                                     content_type="application/json")
        _ret: list[str] = []
        if not name_result.name_available:
            for k, v in name_result.as_dict().items():
                _ret.append(f"{k}: {v}")
            logger.error("\n".join(_ret))
            return CommandResponse.fail()
    except Exception:
        return CommandResponse.fail()

    try:
        poller = kusto_client.databases.begin_create_or_update(resource_group_name=resource_group_name,
                                                               cluster_name=adx_cluster_name,
                                                               database_name=database_name,
                                                               parameters=params_database,
                                                               content_type="application/json")
        poller.wait()
        # check if done
        if not poller.done():
            return CommandResponse.fail()
        # batabase created

        if select:
            logger.info("Updated configuration variable adx_database_name")
            env = Environment()
            env.configuration.set_deploy_var("adx_database_name", database_name)

        _ret: list[str] = [f"Provisioning state: {poller.result().provisioning_state}"]
        logger.info("\n".join(_ret))
        return CommandResponse.success()
    except Exception as ex:
        logger.info(ex)
        return CommandResponse.fail()
