import logging
import pathlib

from typing import Any
from click import Path, command, argument
from azure.mgmt.kusto import KustoManagementClient
from Babylon.commands.azure.adx.script.service.api import AdxScriptService
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@timing_decorator
@pass_kusto_client
@argument("script_file", type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
@inject_context_with_resource({'azure': ['resource_group_name'], 'adx': ['cluster_name', 'database_name']})
def run(context: Any, kusto_client: KustoManagementClient, script_file: pathlib.Path) -> CommandResponse:
    """
    Open SCRIPT_FILE and run it on the database
In the script instances of "<database name>" will be replaced by the actual database name
    """
    apiAdxScript = AdxScriptService()
    apiAdxScript.run(
        context=context,
        script_file=script_file,
        kusto_client=kusto_client
    )
    return CommandResponse.success()
