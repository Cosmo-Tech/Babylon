from pathlib import Path as pathlibPath
from json import loads
from logging import getLogger
from typing import Any
from click import argument, command, option, echo, style
from click import Path as clickPath
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_state, injectcontext, output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("payload_file", type=clickPath(path_type=pathlibPath, exists=True))
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@retrieve_state
def create(state: Any, keycloak_token: str, organization_id: str, workspace_id: str,
           payload_file: clickPath) -> CommandResponse:
    """Create a dataset"""
    _data = [""]
    _data.append("Create a dataset")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    spec = {}
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    payload_string = loads(spec["payload"])
    filename_array = [x["sourceName"] for x in payload_string["parts"]]
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    service = DatasetService(keycloak_token=keycloak_token, state=service_state, spec=spec)
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
