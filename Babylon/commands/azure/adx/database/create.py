import logging

from typing import Any, Optional
from click import Context, argument, command, option, pass_context
from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.kusto.models import ReadWriteDatabase
from azure.mgmt.kusto.models import CheckNameRequest
from Babylon.utils.checkers import check_ascii
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.typing import QueryType
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator

from datetime import timedelta

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_context
@pass_kusto_client
@timing_decorator
@option("--select", "select", is_flag=True, default=True, help="Save this new database in configuration")
@argument("name", type=QueryType(), required=False)
@inject_context_with_resource({
    'api': ['organization_id', 'workspace_key'],
    'azure': ['resource_location', 'resource_group_name'],
    'adx': ['cluster_name']
})
def create(ctx: Context,
           context: Any,
           kusto_client: KustoManagementClient,
           name: Optional[str] = None,
           select: bool = False) -> CommandResponse:
    """
    Create database in ADX cluster
    """
    check_ascii(name)
    organization_id = context['api_organization_id']
    workspace_key = context['api_workspace_key']
    resource_location = context['azure_resource_location']
    resource_group_name = context['azure_resource_group_name']
    adx_cluster_name = context['adx_cluster_name']

    # soft delete period by default 365 days
    # cache period by default 31 days
    params_database = ReadWriteDatabase(location=resource_location,
                                        soft_delete_period=timedelta(days=365),
                                        hot_cache_period=timedelta(days=31))
    name = name or f"{organization_id}-{workspace_key}"
    try:
        name_request = CheckNameRequest(name=name, type="Microsoft.Kusto/clusters/databases")
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

    poller = kusto_client.databases.begin_create_or_update(resource_group_name=resource_group_name,
                                                           cluster_name=adx_cluster_name,
                                                           database_name=name,
                                                           parameters=params_database,
                                                           content_type="application/json")
    poller.wait()
    # check if done
    if not poller.done():
        return CommandResponse.fail()
    # batabase created
    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name="database_name",
                                  var_value=name.lower())
        logger.info(SUCCESS_CONFIG_UPDATED("adx", "database_name"))

    _ret: list[str] = [f"Provisioning state: {poller.result().provisioning_state}"]
    logger.info("\n".join(_ret))
    return CommandResponse.success()
