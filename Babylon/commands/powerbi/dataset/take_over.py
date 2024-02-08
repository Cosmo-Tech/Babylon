import logging
from typing import Any

from click import command
from click import argument
from click import option
from Babylon.commands.powerbi.dataset.service.api import AzurePowerBIDatasetService

from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
@argument("dataset_id", type=QueryType())
@inject_context_with_resource({"powerbi": ["workspace"]})
def take_over(
    context: Any,
    powerbi_token: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Take ownership of a powerbi dataset in the current workspace
    """
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=context)
    service.take_over(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success()
