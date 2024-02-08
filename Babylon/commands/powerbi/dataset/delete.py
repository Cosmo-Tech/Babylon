import logging
from typing import Any, Optional

from click import command
from click import option
from click import argument
from Babylon.commands.powerbi.dataset.service.api import AzurePowerBIDatasetService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
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
@inject_context_with_resource({"powerbi": ["workspace"]})
def delete(
    context: Any,
    powerbi_token: str,
    dataset_id: str,
    workspace_id: Optional[str] = None,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a powerbi dataset in the current workspace
    """
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=context)
    response = service.delete(
        workspace_id=workspace_id,
        force_validation=force_validation,
        dataset_id=dataset_id,
    )
    return CommandResponse.success(response)
