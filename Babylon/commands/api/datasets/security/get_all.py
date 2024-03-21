from logging import getLogger
from typing import Any

from click import command

from Babylon.commands.api.datasets.services.datasets_security_svc import DatasetSecurityService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@retrieve_state
def get_all(state: Any, azure_token: str, organization_id: str, dataset_id: str) -> CommandResponse:
    """
    Get dataset users RBAC access
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    service = DatasetSecurityService(azure_token=azure_token, state=service_state)
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    rbac = response.json()
    return CommandResponse.success(rbac, verbose=True)
