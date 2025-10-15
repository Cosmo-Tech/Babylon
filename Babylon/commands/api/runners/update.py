import pathlib
import click
import json
from logging import getLogger
from typing import Any
from click import command, option, Path, argument
from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
    output_to_file,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@retrieve_state
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--runner-id", "runner_id", type=str)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
def update(
    state: Any,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
    keycloak_token: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update a runner
    """
    _run = [""]
    _run.append("Update a runner")
    _run.append("")
    click.echo(click.style("\n".join(_run), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state["api"]["runner_id"] = (runner_id or state["services"]["api"]["runner_id"])
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    runner_service = RunnerService(state=service_state, spec=spec, keycloak_token=keycloak_token)
    logger.info(f"[api] Updating runner {[state['services']['api']['runner_id']]}")
    response = runner_service.update()
    if response is None:
        return CommandResponse.fail()
    runner = response.json()
    logger.info(json.dumps(runner, indent=2))
    logger.info(f'[api] Runner {[service_state["api"]["runner_id"]]} successfully updated')
    return CommandResponse.success(runner)
