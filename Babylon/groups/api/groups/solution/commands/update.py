from logging import getLogger
from pprint import pformat

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

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@allow_dry_run
@timing_decorator
@pass_solution_api
@pass_environment
@argument("solution_file", type=str)
@require_deployment_key("organization_id", "organization_id")
@option(
    "-s",
    "--select",
    "select",
    type=bool,
    help="Should ...",
    required=False,
)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def update(
    env: Environment,
    solution_api: SolutionApi,
    organization_id: str,
    solution_file: str,
    use_working_dir_file: bool = False,
    select: bool = True,
    dry_run: bool = False,
):
    """Send a JSON or YAML file to the API to create a solution."""

    if dry_run:
        logger.info("DRY RUN - Would call solution_api.create_solution")
        return

    converted_solution_content = get_api_file(
        api_file_path=solution_file,
        use_working_dir_file=use_working_dir_file,
        logger=logger,
    )
    if not converted_solution_content:
        logger.error("Error : can not get correct connector definition, please check your Solution.YAML file")
        return

    try:
        retrieved_data = solution_api.create_solution(
            organization_id=organization_id, solution=converted_solution_content
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} does not exists.")
        return

    logger.debug(pformat(retrieved_data))
    logger.info(f"Created new solution with id: {retrieved_data['id']}")
