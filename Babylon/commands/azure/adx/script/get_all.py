import logging

from typing import Any
from azure.mgmt.kusto import KustoManagementClient
from click import command
from Babylon.commands.azure.adx.script.service.api import AdxScriptService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_kusto_client
@inject_context_with_resource({'azure': ['resource_group_name'], 'adx': ['cluster_name', 'database_name']})
def get_all(
    context: Any,
    kusto_client: KustoManagementClient,
) -> CommandResponse:
    """
    List scripts on the database
    """
    apiAdxScript = AdxScriptService(kusto_client=kusto_client, state=context)
    scripts = apiAdxScript.get_all()
    return CommandResponse.success(scripts, verbose=True)
