import logging

from typing import Any, Optional
from click import command
from click import argument
from click import option
from Babylon.commands.powerbi.dataset.parameters.service.api import AzurePowerBIParamsService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option(
    "--parameter",
    "params",
    type=(QueryType(), QueryType()),
    multiple=True,
    required=True,
    help="Report parameter",
)
@option("--workspace-id", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
@argument("dataset_id", type=QueryType())
@inject_context_with_resource({"powerbi": ["workspace"]})
def update(
    context: Any,
    powerbi_token: str,
    dataset_id: str,
    params: list[tuple[str, str]],
    workspace_id: Optional[str] = None,
) -> CommandResponse:
    """
    Update parameters of a given dataset
    """
    api_powerbi = AzurePowerBIParamsService(powerbi_token=powerbi_token, state=context)
    api_powerbi.update(workspace_id=workspace_id, params=params, dataset_id=dataset_id)
    return CommandResponse.success()
