from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import option

from ....utils.decorators import require_deployment_key
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
@require_deployment_key("simulator_repository", "simulator_repository")
@require_deployment_key("simulator_version", "simulator_version")
@argument("solution-name", type=QueryType())
@option(
    "-d",
    "--description",
    "solution_description",
    help="New solution description",
)
@option(
    "-i",
    "--solution-file",
    "solution_file",
    type=str,
    required=True,
    help="Your custom solution description file",
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
           simulator_repository: str,
           simulator_version: str,
           solution_name: str,
           solution_description: Optional[str] = None,
           solution_file: Optional[str] = None,
           select: bool = False) -> CommandResponse:
    """
    Register new solution by sending description file to the API.
    Edit and use the solution file template located in `API/solution.json`
    """
    env = Environment()
    details = env.fill_template(solution_file,
                                data={
                                    "solution_key": solution_name.replace(" ", ""),
                                    "solution_name": solution_name,
                                    "simulator_version": simulator_version,
                                    "simulator_repository": simulator_repository,
                                    "solution_description": solution_description
                                })
    response = oauth_request(f"{api_url}/organizations/{organization_id}/solutions",
                             azure_token,
                             type="POST",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(f"Successfully created dataset {solution['id']}")
    if select:
        logger.info("Updated configuration variables with solution_id")
        env.configuration.set_deploy_var("solution_id", solution["id"])
    return CommandResponse.success(solution, verbose=True)
