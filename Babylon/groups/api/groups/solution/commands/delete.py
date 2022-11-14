from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.interactive import confirm_deletion

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@describe_dry_run("Would call **solution_api.delete_solution** to delete an solution")
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
)
@option(
    "-i",
    "--solution-file",
    "solution_file",
    help="Your Solution description file path",
)
@argument("solution-id", required=False)
def delete(
    solution_api: SolutionApi,
    organization_id: str,
    solution_id: Optional[str] = None,
    solution_file: Optional[str] = None,
    force_validation: Optional[bool] = False,
    use_working_dir_file: Optional[bool] = False,
) -> Optional[str]:
    """Unregister a solution via Cosmotech APi."""

    if not solution_id:
        if not solution_file:
            logger.error("No id passed as argument or option \n"
                         "Use -i option to pass an json or yaml file containing an solution id.")
            return

        converted_solution_content = get_api_file(
            api_file_path=solution_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
        if not converted_solution_content:
            logger.error("Error : can not get correct solution definition, please check your Solution.YAML file")
            return

        solution_id = converted_solution_content.get("id") or converted_solution_content.get("solution_id")
        if not solution_id:
            logger.error("Can not get solution id, please check your file")
            return

    try:
        solution_api.find_solution_by_id(solution_id=solution_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Solution {solution_id} not found in organization {organization_id}.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return
    except ServiceException:
        logger.error(f"Organization with id {organization_id} not found.")
        return

    if not force_validation and not confirm_deletion("solution", solution_id):
        return

    logger.info(f"Deleting solution {solution_id}")

    try:
        solution_api.delete_solution(organization_id=organization_id, solution_id=solution_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Solution {solution_id} not found in organization {organization_id}.")
        return
    except ForbiddenException:
        logger.error(f"You are not allowed to delete the Solution : {solution_id}")
        return

    logger.info(f"Solutions {solution_id} of organization {organization_id} deleted.")

    return solution_id
