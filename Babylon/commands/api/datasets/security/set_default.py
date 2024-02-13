import json
import logging

from click import command, option

from Babylon.commands.api.datasets.security.service.api import DatasetSecurityService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state, timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@output_to_file
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@retrieve_state
def set_default(state: dict, azure_token: str, role: str, organization_id: str, dataset_id: str) -> CommandResponse:
    """
    Update dataset default security
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    details = json.dumps({"role": role})
    service = DatasetSecurityService(azure_token=azure_token, state=service_state)
    response = service.set_default(details=details)
    rbac = response.json()
    return CommandResponse.success(rbac, verbose=True)
