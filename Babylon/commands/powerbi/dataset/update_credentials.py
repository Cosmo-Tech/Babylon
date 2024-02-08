import logging

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.commands.powerbi.dataset.service.api import AzurePowerBIDatasetService
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@argument("dataset_id", type=QueryType())
@inject_context_with_resource({"powerbi": ["workspace"]})
def update_credentials(
    context: Any,
    powerbi_token: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Update azure credentials of a given datasource
    """
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=context)
    service.update_credentials(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse()
