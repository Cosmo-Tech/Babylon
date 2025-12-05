from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("tag", type=str, nargs=-1)
@output_to_file
@retrieve_state
def search(
    state: Any, config: Any, keycloak_token: str, organization_id: str, workspace_id: str, tag: tuple[str, ...]
) -> CommandResponse:
    """Get dataset with the given tag from the organization

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       TAG : A specific tag used to retrieve the dataset
    """
    _data = [""]
    _data.append("Get dataset with the given tag")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    logger.info(f"Searching dataset by tag {[tag]}")
    service = DatasetService(keycloak_token=keycloak_token, state=services_state, config=config)
    response = service.search(tag=tag)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    logger.info(f"Retrieved datasets {[d.get('id') for d in dataset]}")
    return CommandResponse.success(dataset)
