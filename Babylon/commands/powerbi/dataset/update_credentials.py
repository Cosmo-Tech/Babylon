import logging

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.commands.powerbi.dataset.services.powerbi_api_svc import AzurePowerBIDatasetService
from Babylon.utils.response import CommandResponse

from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@argument("dataset_id", type=str)
@retrieve_state
def update_credentials(
    state: Any,
    powerbi_token: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Update azure credentials of a given datasource
    """
    service_state = state['services']
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=service_state)
    service.update_credentials(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse()
