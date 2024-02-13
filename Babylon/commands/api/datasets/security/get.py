from logging import getLogger
from typing import Any

from click import argument, command

from Babylon.commands.api.datasets.security.service.api import DatasetSecurityService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@argument("identity_id", type=str)
@retrieve_state
def get(state: Any, azure_token: str, identity_id: str, organization_id: str, dataset_id: str) -> CommandResponse:
    """
    Get dataset user RBAC access
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    service = DatasetSecurityService(azure_token=azure_token, state=service_state)
    response = service.get(id=identity_id)
    rbac = response.json()
    return CommandResponse.success(rbac, verbose=True)
