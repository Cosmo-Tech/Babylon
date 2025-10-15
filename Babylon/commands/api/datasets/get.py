import click
import json

from logging import getLogger
from typing import Any
from click import command, option
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--dataset-id", "dataset_id", type=str)
@retrieve_state
def get(state: Any, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str) -> CommandResponse:
    """Get a dataset"""
    _data = [""]
    _data.append("Get dataset details")
    _data.append("")
    click.echo(click.style("\n".join(_data), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    service_state["api"]["dataset_id"] = (dataset_id or service_state["api"]["dataset_id"])
    service = DatasetService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Searching dataset {[service_state['api']['dataset_id']]}")
    response = service.get()
    if response is None:
        return CommandResponse.fail()
    dataset = response.json()
    logger.info(json.dumps(dataset, indent=2))
    return CommandResponse.success(dataset)
