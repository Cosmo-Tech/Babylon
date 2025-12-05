from json import loads
from logging import getLogger
from pathlib import Path as pathlibPath
from typing import Any

from click import Path as clickPath
from click import argument, command, echo, style

from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("dataset_id", required=True)
@argument("payload_file", type=clickPath(path_type=pathlibPath, exists=True))
@retrieve_state
def create_part(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    payload_file: clickPath,
) -> CommandResponse:
    """
    Create a dataset part

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       DATASET_ID: The unique identifier of the datatset
       PAYLOAD_FILE : Path to the manifest file used to create the dataset
    """
    _data = [""]
    _data.append("Create a dataset part")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    spec = {}
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    payload_string = loads(spec["payload"])
    filename = payload_string["sourceName"]
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    service = DatasetService(keycloak_token=keycloak_token, state=services_state, spec=spec, config=config)
    response = service.create_part(filename, dataset_id)
    if response is None:
        return CommandResponse.fail()
    dataset_part = response.json()
    logger.info(f"Dataset part {[dataset_part.get('id')]} successfully created")
    return CommandResponse.success(dataset_part)
