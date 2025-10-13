from logging import getLogger
from typing import Any

from click import argument
from click import command, option

from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@argument("tag", type=str)
@output_to_file
@retrieve_state
def search(state: Any, keycloak_token: str, organization_id: str, tag: str) -> CommandResponse:
    """Get dataset with the given tag from the organization"""
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    logger.info(f"Searching dataset by tag: {tag}")
    service = DatasetService(keycloak_token=keycloak_token, state=service_state)
    response = service.search(tag=tag)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    return CommandResponse.success(dataset, verbose=True)
