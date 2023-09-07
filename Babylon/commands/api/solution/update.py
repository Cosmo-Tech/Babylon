import pathlib
from logging import getLogger

from click import Path
from click import argument
from click import command
from click import option

from ....utils.credentials import pass_azure_token
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.environment import Environment
from ....utils.request import oauth_request
from ....utils.response import CommandResponse
from ....utils.typing import QueryType
from ....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@option("--solution-id", "solution_id", type=QueryType(), default="%deploy%solution_id")
@argument("solution_file", type=Path(path_type=Patth(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)))
@option("--organization-id", "organization_id", type=QueryType(), default="%deploy%organization_id")
@output_to_file
def update(api_url: str, azure_token: str, organization_id: str, solution_id: str,
           solution_file: pathlib.Path) -> CommandResponse:
    """
    Register a solution by sending description file to the API.
    See the API files to edit your own file manually if needed
    """
    env = Environment()
    solution_details = env.working_dir.get_file_content(solution_file)
    solution_key = solution_details["name"].replace(" ", "")
    logger.debug(solution_details["name"])
    details = env.fill_template(solution_file, data={"solution_key": solution_key})
    if solution_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions/{solution_id}",
                             azure_token,
                             type="PATCH",
                             data=details.encode("utf-8"))
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(f"Successfully updated solution {solution['id']}")
    return CommandResponse.success(solution, verbose=True)
