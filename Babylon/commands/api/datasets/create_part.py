from pathlib import Path as pathlibPath
from json import loads
from logging import getLogger
from typing import Any
from click import argument, command, option, echo, style
from click import Path as clickPath
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@argument("payload_file", type=clickPath(path_type=pathlibPath, exists=True))
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@retrieve_state
def create_part(state: Any, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str,
                payload_file: clickPath) -> CommandResponse:
    """Create a dataset part"""
    _data = [""]
    _data.append("Create a dataset part")
    _data.append("")
    echo(style("\n".join(_data), bold=True, fg="green"))
    spec = {}
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    payload_string = loads(spec["payload"])
    filename = payload_string["sourceName"]
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    service_state["api"]["dataset_id"] = (dataset_id or service_state["api"]["dataset_id"])
    service = DatasetService(keycloak_token=keycloak_token, state=service_state, spec=spec)
    response = service.create_part(filename)
    if response is None:
        return CommandResponse.fail()
    dataset_part = response.json()
    logger.info(f"Dataset part {[dataset_part.get('id')]} successfully created")
    return CommandResponse.success(dataset_part)
