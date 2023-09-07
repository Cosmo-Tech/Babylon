import pathlib
from logging import getLogger
from typing import Optional

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
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@argument("solution_file", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
@option(
    "--solution-name",
    "solution_name",
    type=QueryType(),
    help="Your custom solution name",
)
@option("-s", "--select", "select", is_flag=True, default=True, help="Select the created solution ?")
@output_to_file
def create(
    api_url: str,
    azure_token: str,
    organization_id: str,
    solution_file: pathlib.Path,
    select: bool,
    solution_name: Optional[str] = None,
) -> CommandResponse:
    """
    Register new solution by sending description file to the API.
    See the API files to edit your own file manually if needed
    """
    env = Environment()
    solution_details = env.working_dir.get_file_content(solution_file)

    solution_key = solution_name.replace(" ", "") if solution_name else solution_details["name"].replace(" ", "")
    logger.debug(solution_details["name"])
    details = env.fill_template(solution_file, data={"solution_key": solution_key, "solution_name": solution_name})
    if solution_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions",
                             azure_token,
                             type="POST",
                             data=details.encode("utf-8"))
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(f"Successfully created dataset {solution['id']}")
    if select:
        logger.info("Updated configuration variables with solution_id")
        env.configuration.set_deploy_var("solution_id", solution["id"])
    return CommandResponse.success(solution, verbose=True)
