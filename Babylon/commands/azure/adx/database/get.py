import logging

from typing import Any, Optional
from click import Context, argument, command, option, pass_context
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.typing import QueryType
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@timing_decorator
@pass_kusto_client
@option("-s", "--select", "select", is_flag=True, default=True, help="Save this adx database name in configuration")
@argument("name", type=QueryType(), required=False)
@inject_context_with_resource({
    'azure': ['resource_group_name'],
    'adx': ['cluster_name', 'database_name']
},
                              required=False)
def get(
    ctx: Context,
    context: Any,
    kusto_client: KustoManagementClient,
    select: bool,
    name: Optional[str] = None,
) -> CommandResponse:
    """
    Get database from ADX cluster
    """
    adx_cluster_name = context['adx_cluster_name']
    if not name:
        logger.error(f"You trying to {ctx.command.name} '{ctx.parent.command.name}' referenced in configuration")
        logger.error(f"Current value: '{context['adx_database_name']}'")
    adx_database_name = name or context['adx_database_name']
    if not adx_database_name:
        logger.error("Database name is missing")
        return CommandResponse.fail()
    resource_group_name = context['azure_resource_group_name']
    try:
        database = kusto_client.databases.get(resource_group_name=resource_group_name,
                                              cluster_name=adx_cluster_name,
                                              database_name=adx_database_name)
        _ret: list[str] = []
        for k, v in database.as_dict().items():
            _ret.append(f"{k}:{v}")
        logger.info("\n".join(_ret))
        if select:
            env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                      var_name="database_name",
                                      var_value=adx_database_name)
            logger.info(SUCCESS_CONFIG_UPDATED("adx", "database_name"))
        return CommandResponse.success()
    except Exception as ex:
        logger.info(ex)
        return CommandResponse.fail()
