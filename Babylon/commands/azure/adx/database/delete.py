import logging

from typing import Any, Optional
from click import argument, command, option
from azure.mgmt.kusto import KustoManagementClient
from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService
from Babylon.utils.typing import QueryType
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_kusto_client
@option(
    "--current",
    "current",
    type=QueryType(),
    is_flag=True,
    help="Delete database adx referenced in configuration",
)
@argument("name", type=QueryType())
@inject_context_with_resource(
    {"azure": ["resource_group_name"], "adx": ["cluster_name", "database_name"]}
)
def delete(
    context: Any,
    kusto_client: KustoManagementClient,
    name: Optional[str] = None,
    current: bool = False,
) -> CommandResponse:
    """
    Delete database in ADX cluster
    """
    apiAdxDatabase = AdxDatabaseService(kusto_client=kusto_client, state=context)
    apiAdxDatabase.delete(
        name=name,
        context=context,
        current=current,
    )
    return CommandResponse.success()
