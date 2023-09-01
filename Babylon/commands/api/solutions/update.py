import pathlib

from logging import getLogger
from typing import Any
from click import argument, command
from click import option
from click import Path
from Babylon.utils.messages import SUCCESS_UPDATED
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option(
    "--file",
    "solution_file",
    type=Path(path_type=pathlib.Path),
    help="Your custom solution description file yaml",
)
@argument("id")
@inject_context_with_resource({"api": ['url', 'organization_id', 'solution_id']})
def update(context: Any, azure_token: str, id: str, solution_file: pathlib.Path) -> CommandResponse:
    """
    Update a solution
    """
    solution_id = id or context['api_solution_id']
    path_file = f"{env.context_id}.{env.environ_id}.solution.yaml"
    solution_file = solution_file or env.working_dir.payload_path / path_file
    if not solution_file.exists():
        return CommandResponse.fail()
    details = env.fill_template(solution_file)
    response = oauth_request(
        f"{context['api_url']}/organizations/{context['api_organization_id']}/solutions/{solution_id}",
        azure_token,
        type="PATCH",
        data=details)
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(SUCCESS_UPDATED("solution", solution_id))
    return CommandResponse.success(solution, verbose=True)
