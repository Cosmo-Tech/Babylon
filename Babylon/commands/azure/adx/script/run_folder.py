import pathlib
from typing import Any

from click import Path, command, pass_context, argument
from azure.mgmt.kusto import KustoManagementClient
from Babylon.commands.azure.adx.script.service.api import AdxScriptService
from Babylon.utils.decorators import (
    inject_context_with_resource,
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
@inject_context_with_resource(
    {"azure": ["resource_group_name"], "adx": ["cluster_name", "database_name"]}
)
def run_folder(
    context: Any,
    kusto_client: KustoManagementClient,
    script_folder: pathlib.Path,
) -> CommandResponse:
    """
    Run all script files (.kql) from SCRIPT_FOLDER
    """
    apiAdxScript = AdxScriptService()
    apiAdxScript.run_folder(
        context=context, script_folder=script_folder, kusto_client=kusto_client
    )
    return CommandResponse.success()
