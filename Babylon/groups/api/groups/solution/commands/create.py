from logging import getLogger
from pprint import pformat
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import pass_environment
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.environment import Environment
from ......utils import TEMPLATE_FOLDER_PATH

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@allow_dry_run
@timing_decorator
@pass_solution_api
@pass_environment
@argument("solution_file", required=False)
@require_deployment_key("solution_version", "solution_version")
@require_deployment_key("solution_repository", "solution_repository")
@require_deployment_key("organization_id", "organization_id")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    type=bool,
    help="Should the path be relative to the working directory ?",
)
@option(
    "-n",
    "--name",
    "solution_name",
    required=True,
    help="New solution name",
)
@option(
    "-d",
    "--description",
    "solution_description",
    help="New solution description",
)
@option(
    "-s",
    "--select",
    "select",
    type=bool,
    help="Select this new Solution as babylon context solution ?",
    default=True,
)
def create(
    env: Environment,
    solution_api: SolutionApi,
    organization_id: str,
    solution_name: str,
    solution_version: str,
    solution_repository: str,
    solution_file: str,
    select: bool,
    solution_description: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
    dry_run: bool = False,
):
    """Send a JSON or YAML file to the API to create a solution."""

    if dry_run:
        logger.info("DRY RUN - Would call solution_api.create_solution")
        return

    converted_solution_content = get_api_file(
        api_file_path=solution_file
        if solution_file
        else f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Solution.yaml",
        use_working_dir_file=use_working_dir_file if solution_file else False,
        logger=logger,
    )
    if not converted_solution_content:
        logger.error("Error : can not get correct solution definition, please check your Solution.YAML file")
        return

    if not solution_description and "solution_description" not in converted_solution_content:
        converted_solution_content["description"] = solution_name

    converted_solution_content["name"] = solution_name
    converted_solution_content["key"] = solution_name.replace(" ", "")
    converted_solution_content["version"] = solution_version
    converted_solution_content["repository"] = solution_repository

    try:
        retrieved_solution = solution_api.create_solution(
            organization_id=organization_id, solution=converted_solution_content
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} does not exists.")
        return

    if select:
        env.configuration.set_deploy_var("solution_id", retrieved_solution["id"])

    logger.debug(pformat(retrieved_solution))
    logger.info(f"Created new solution with id: {retrieved_solution['id']}")
