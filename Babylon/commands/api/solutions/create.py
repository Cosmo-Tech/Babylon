import pathlib

from logging import getLogger
from posixpath import basename
import sys
from typing import Any
from click import Context, argument, pass_context
from click import command
from click import option
from click import Path
from Babylon.utils.checkers import check_ascii
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED, SUCCESS_CREATED
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


@command()
@pass_context
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option(
    "-f",
    "--file",
    "solution_file",
    type=Path(path_type=pathlib.Path),
    help="Your custom solution description file (yaml or json)",
)
@option("-s", "--select", "select", is_flag=True, default=True, help="Save this new solution in configuration")
@argument("name", type=QueryType())
@inject_context_with_resource({"api": ['url', 'organization_id'], 'acr': ['simulator_repository', 'simulator_version']})
def create(ctx: Context, context: Any, azure_token: str, name: str, solution_file: pathlib.Path,
           select: bool) -> CommandResponse:
    """
    Register new solution
    """
    check_ascii(name)
    path_file = f"{env.context_id}.{env.environ_id}.solution.yaml"
    t_file = solution_file or env.working_dir.payload_path / path_file
    if not t_file.exists():
        logger.error(f"No such file: '{basename(t_file)}' in .payload directory")
        sys.exit(1)

    details = env.fill_template(t_file,
                                data={
                                    "key": name.replace(" ", ""),
                                    "name": name,
                                    'tag': env.context_id.capitalize()
                                })
    response = oauth_request(f"{context['api_url']}/organizations/{context['api_organization_id']}/solutions",
                             azure_token,
                             type="POST",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name="solution_id",
                                  var_value=solution["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("solution", "solution_id"))
    logger.info(SUCCESS_CREATED("solution", solution["id"]))
    return CommandResponse.success(solution, verbose=True)
