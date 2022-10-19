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
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@allow_dry_run
@timing_decorator
@pass_solution_api
@argument("solution_file")
@require_deployment_key("organization_id", "organization_id")
@require_deployment_key("solution_id", "solution_id")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    type=bool,
    help="Should the path be relative to the working directory ?",
)
def update(
    solution_api: SolutionApi,
    solution_file: str,
    organization_id: str,
    solution_id: str,
    use_working_dir_file: Optional[bool] = False,
    dry_run: bool = False,
):
    """Send a JSON or YAML file to the API to update a solution."""

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
        retrieved_solution = solution_api.update_solution(solution_id=solution_id,
            organization_id=organization_id, solution=converted_solution_content
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Solution {solution_id} does not exists in organization {organization_id}.")
        return

    logger.debug(pformat(retrieved_solution))
    logger.info(f"Created new solution with id: {retrieved_solution['id']}")
