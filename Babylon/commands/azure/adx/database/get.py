import logging

from typing import Any, Optional
from click import argument, command
from azure.mgmt.kusto import KustoManagementClient
from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService
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
@timing_decorator
@pass_kusto_client
@argument("name", type=QueryType(), required=False)
@inject_context_with_resource(
    {"azure": ["resource_group_name"], "adx": ["cluster_name", "database_name"]},
    required=False,
)
def get(
    context: Any,
    kusto_client: KustoManagementClient,
    name: Optional[str] = None,
) -> CommandResponse:
    """
    Get database from ADX cluster
    """
    service = AdxDatabaseService(kusto_client=kusto_client, state=context)
    service.get(
        name=name,
    )
    return CommandResponse.success()
