from json import loads
from logging import getLogger
from pathlib import Path as pathlibPath
from typing import Any

from click import Path as clickPath
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
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("payload_file", type=clickPath(path_type=pathlibPath, exists=True))
@retrieve_state
def create(
    state: Any, config: Any, keycloak_token: str, organization_id: str, workspace_id: str, payload_file: clickPath
) -> CommandResponse:
    """
    Create a dataset

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       PAYLOAD_FILE : Path to the manifest file used to create the dataset
    """
    _data = [""]
    _data.append("Create a dataset")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    spec = {}
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    payload_string = loads(spec["payload"])
    filename_array = [x["sourceName"] for x in payload_string["parts"]]
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    service = DatasetService(keycloak_token=keycloak_token, state=services_state, spec=spec, config=config)
    response = service.create(filename_array)
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    state["services"]["api"]["dataset_id"] = dataset.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(f"Dataset {[dataset.get('id')]} successfully created")
    return CommandResponse.success(dataset)
