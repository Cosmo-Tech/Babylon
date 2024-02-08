import logging

from typing import Any
from azure.mgmt.kusto import KustoManagementClient
from click import command
from Babylon.commands.azure.adx.script.service.api import AdxScriptService
from Babylon.utils.decorators import (
    retrieve_state,
    wrapcontext,
)
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
@retrieve_state
def get_all(state: Any, kusto_client: KustoManagementClient) -> CommandResponse:
    """
    List scripts on the database
    """
    service = AdxScriptService(kusto_client=kusto_client, state=state)
    scripts = service.get_all()
    return CommandResponse.success(scripts, verbose=True)
