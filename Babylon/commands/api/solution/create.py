from logging import getLogger
import pathlib

from click import argument
from click import command
from click import option
from click import Path

from ....utils.yaml_utils import yaml_to_json
from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.environment import Environment
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request

logger = getLogger("Babylon")


@command()
@timing_decorator
@pass_azure_token("csm_api")
@require_platform_key("api_url")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@argument("solution-name", type=QueryType())
@option(
    "-i",
    "--solution-file",
    "solution_file",
    type=Path(path_type=pathlib.Path),
    required=True,
    help="Your custom solution description file (yaml or json)",
)
@option(
    "-s",
    "--select",
    "select",
    is_flag=True,
    help="Select this new solution in configuration ?",
)
@output_to_file
def create(azure_token: str,
           api_url: str,
           organization_id: str,
           solution_name: str,
           solution_file: pathlib.Path,
           select: bool = False) -> CommandResponse:
    """
    Register new solution by sending description file to the API.
    See the API files to edit your own file manually if needed
    """
    env = Environment()
    details = env.fill_template(solution_file,
                                data={
                                    "solution_key": solution_name.replace(" ", ""),
                                    "solution_name": solution_name
                                })
    if solution_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions",
                             azure_token,
                             type="POST",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(f"Successfully created solution {solution['id']}")
    if select:
        logger.info("Updated configuration variables with solution_id")
        env.configuration.set_deploy_var("solution_id", solution["id"])
    return CommandResponse.success(solution, verbose=True)
