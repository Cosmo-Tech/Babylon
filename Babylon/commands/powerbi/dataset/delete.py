import logging
from typing import Any, Optional

from click import command
from click import option
from click import argument
from Babylon.commands.powerbi.dataset.service.api import AzurePowerBIDatasetService
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("dataset_id", type=QueryType())
@retrieve_state
def delete(
    state: Any,
    powerbi_token: str,
    dataset_id: str,
    workspace_id: Optional[str] = None,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a powerbi dataset in the current workspace
    """
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=state)
    response = service.delete(
        workspace_id=workspace_id,
        force_validation=force_validation,
        dataset_id=dataset_id,
    )
    return CommandResponse.success(response)
