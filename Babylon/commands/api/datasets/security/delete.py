import logging

from click import argument, command, option

from Babylon.commands.api.datasets.services.security import DatasetSecurityService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token("csm_api")
@output_to_file
@option("--organization-id", "organization_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@argument("identity_id", type=str)
@retrieve_state
def delete(state: dict, azure_token: str, identity_id: str, organization_id: str, dataset_id: str) -> CommandResponse:
    """
    Delete dataset users RBAC access
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    service = DatasetSecurityService(azure_token=azure_token, state=service_state)
    response = service.delete(id=identity_id)
    return CommandResponse.success(response, verbose=True)
