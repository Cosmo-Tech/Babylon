import pathlib

from logging import getLogger
from typing import Any
from click import Choice, command
from click import option
from click import argument
from click import Path
from Babylon.commands.api.solutions.handler.service.api import ApiSolutionHandleService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    retrieve_state,
    wrapcontext,
)
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@timing_decorator
@option(
    "--organization-id",
    "organization_id",
    type=str,
    help="Organization id or referenced in configuration",
)
@option(
    "--solution-id",
    "solution_id",
    type=str,
    help="Solution id or referenced in configuration",
)
@option(
    "--run-template",
    "run_template_id",
    help="The run Template identifier name example: 'Sensitive analysis'",
    type=str,
    required=True,
)
@option("--override", "override", is_flag=True, help="Override handler solution")
@argument(
    "handler_id",
    type=Choice([
        "validator",
        "prerun",
        "engine",
        "postrun",
        "scenariodata_transform",
        "parameters_handler",
    ]),
)
@argument("handler_path", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def upload(
    state: Any,
    azure_token: str,
    handler_id: str,
    run_template_id: str,
    organization_id: str,
    solution_id: str,
    handler_path: pathlib.Path,
    override: bool = False,
) -> CommandResponse:
    """Upload a solution handler zip to the solution"""
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    service = ApiSolutionHandleService(state=service_state, azure_token=azure_token)
    service.upload(run_template_id=run_template_id, handler_id=handler_id, handler_path=handler_path, override=override)
    return CommandResponse.success()
