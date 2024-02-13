from logging import getLogger
from typing import Any
from click import command
from click import option
from click import argument
from Babylon.commands.api.solutions.handler.service.api import SolutionHandleService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    retrieve_state,
    timing_decorator,
    wrapcontext,
)
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@timing_decorator
@output_to_file
@option(
    "--organization-id",
    "organization_id",
    type=str,
    help="Organization id or referenced in state",
)
@option(
    "--solution-id",
    "solution_id",
    type=str,
    help="Solution id or referenced in state",
)
@option(
    "--run-template",
    "run_template_id",
    help="The run Template identifier",
    required=True,
    type=str,
)
@argument("handler_id", type=str)
@retrieve_state
def download(
    state: Any,
    azure_token: str,
    organization_id: str,
    solution_id: str,
    handler_id: str,
    run_template_id: str,
) -> CommandResponse:
    """Download a solution handler zip from the solution"""
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["solution_id"] = solution_id or service_state["api"]["solution_id"]
    service = SolutionHandleService(state=service_state, azure_token=azure_token)
    service.download(run_template_id=run_template_id, handler_id=handler_id)
    return CommandResponse.success()
