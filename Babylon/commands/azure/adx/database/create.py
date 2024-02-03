import logging

from typing import Any, Optional
from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.decorators import timing_decorator
from click import argument, command, option
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_kusto_client
@timing_decorator
@argument("name", type=QueryType(), required=False)
@option(
    "--retention", "retention", default=365, help="Retention days", show_default=True
)
@inject_context_with_resource(
    {
        "api": ["organization_id", "workspace_key"],
        "azure": ["resource_location", "resource_group_name"],
        "adx": ["cluster_name"],
    }
)
def create(
    context: Any,
    kusto_client: KustoManagementClient,
    retention: int,
    name: Optional[str] = None,
) -> CommandResponse:
    """
    Create database in ADX cluster
    """
    apiAdxDatabase = AdxDatabaseService(kusto_client=kusto_client, state=context)
    apiAdxDatabase.create(name=name, context=context, retention=retention)
    return CommandResponse.success()
