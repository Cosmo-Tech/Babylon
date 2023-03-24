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
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("solution_id", required=True, type=QueryType())
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option(
    "-i",
    "--solution-file",
    "solution_file",
    type=Path(path_type=pathlib.Path),
    required=True,
    help="Your custom solution description file (yaml or json)",
)
@output_to_file
def update(api_url: str, azure_token: str, organization_id: str, solution_id: str,
           solution_file: pathlib.Path) -> CommandResponse:
    """Register a solution by sending description file to the API."""
    env = Environment()
    details = env.fill_template(solution_file)
    if solution_file.suffix == ".yaml":
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions/{solution_id}",
                             azure_token,
                             type="PATCH",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(f"Successfully updated solution {solution['id']}")
    return CommandResponse.success(solution, verbose=True)
