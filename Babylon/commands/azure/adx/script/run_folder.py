import pathlib
from typing import Any

from click import Path, command, pass_context, argument
from azure.mgmt.kusto import KustoManagementClient
from Babylon.commands.azure.adx.services.script import AdxScriptService
from Babylon.utils.decorators import (
    retrieve_state,
    timing_decorator,
    wrapcontext,
)
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.response import CommandResponse


@command()
@wrapcontext()
@timing_decorator
@pass_context
@pass_kusto_client
@argument(
    "script_folder",
    type=Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        path_type=pathlib.Path,
    ),
)
@retrieve_state
def run_folder(
    state: Any,
    kusto_client: KustoManagementClient,
    script_folder: pathlib.Path,
) -> CommandResponse:
    """
    Run all script files (.kql) from SCRIPT_FOLDER
    """
    service_state = state['services']
    service = AdxScriptService(kusto_client=kusto_client, state=service_state)
    service.run_folder(script_folder=script_folder)
    return CommandResponse.success()
