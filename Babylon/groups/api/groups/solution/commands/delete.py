from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import confirm
from click import make_pass_decorator
from click import option
from click import prompt
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
@pass_solution_api
@timing_decorator
@require_deployment_key("organization_id", "organization_id")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
    type=bool,
)
@option(
    "--from-file",
    "from_file",
    is_flag=True,
    help="In case the solution id is retrieved from a file",
)
@argument("solution_id")
def delete(
    solution_api: SolutionApi,
    organization_id: str,
    solution_id: str,
    dry_run: bool = False,
    from_file: bool = False,
    use_working_dir_file: Optional[bool] = False,
    force_validation: bool = False,
):
    """Unregister a solution via Cosmotech APi."""

    if dry_run:
        logger.info("DRY RUN - Would call solution_api.delete_solution")
        return

    if from_file:
        solution_file = solution_id
        converted_solution_content = get_api_file(
            api_file_path=solution_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
        if converted_solution_content["id"]:
            solution_id = converted_solution_content["id"]
        elif converted_solution_content["solution_id"]:
            solution_id = converted_solution_content["solution_id"]
        else:
            logger.error(f"Could not found solution id in {solution_file}.")
            return

    try:
        solution_api.find_solution_by_id(solution_id=solution_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Solution {solution_id} does not exists in organization {organization_id}.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return

    if not force_validation:

        if not confirm(f"You are trying to delete solution {solution_id} solutions of organization {organization_id} \n"
                       "Do you want to continue?"):
            logger.info("Solution deletion aborted.")
            return

        confirm_solution_id = prompt("Confirm solution id ")
        if confirm_solution_id != solution_id:
            logger.error("The solution id you have type didn't mach with solution you are trying to delete id")
            return

    logger.info(f"Deleting solution {solution_id}")

    try:
        solution_api.delete_solution(organization_id=organization_id, solution_id=solution_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Solution {solution_id} does not exists in organization {organization_id}.")
        return
    logger.info(f"Solutions {solution_id} of organization {organization_id} deleted.")
