import json
import logging

from click import argument, command, option

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
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("identity_id", type=str)
@retrieve_state
def update(state: dict, azure_token: str, identity_id: str, email: str, role: str, organization_id: str,
           dataset_id: str) -> CommandResponse:
    """
    Update dataset users RBAC access
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["dataset_id"] = dataset_id or service_state["api"]["dataset_id"]
    details = json.dumps({"id": email, "role": role})
    service = DatasetSecurityService(azure_token=azure_token, state=service_state)
    response = service.update(id=identity_id, details=details)
    if response is None:
        return CommandResponse.fail()
    rbac = response.json()
    return CommandResponse.success(rbac, verbose=True)
