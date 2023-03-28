from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ....utils.api import get_api_file
from ....utils.decorators import describe_dry_run
from ....utils.decorators import require_deployment_key
from ....utils.decorators import timing_decorator
from ....utils.interactive import confirm_deletion
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **solution_api.delete_solution** to delete an solution")
@timing_decorator
@pass_api_client
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
@argument("solution-id", required=False, type=QueryType())
def delete(
    api_client: ApiClient,
    organization_id: str,
    solution_id: Optional[str] = None,
    solution_file: Optional[str] = None,
    force_validation: Optional[bool] = False,
    use_working_dir_file: Optional[bool] = False,
) -> CommandResponse:
    """Unregister a solution via Cosmotech APi."""
    solution_api = SolutionApi(api_client)

    if not solution_id:
        if not solution_file:
            logger.error("No id passed as argument or option \n"
                         "Use -i option to pass an json or yaml file containing an solution id.")
            return CommandResponse.fail()

        converted_solution_content = get_api_file(api_file_path=solution_file,
                                                  use_working_dir_file=use_working_dir_file)
        if not converted_solution_content:
            logger.error("Error : can not get correct solution definition, please check your Solution.YAML file")
            return CommandResponse.fail()

        solution_id = converted_solution_content.get("id") or converted_solution_content.get("solution_id")
        if not solution_id:
            logger.error("Can not get solution id, please check your file")
            return CommandResponse.fail()

    try:
        solution_api.find_solution_by_id(solution_id=solution_id, organization_id=organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id {organization_id} not found.")
        return CommandResponse.fail()

    if not force_validation and not confirm_deletion("solution", solution_id):
        return CommandResponse.fail()

    logger.info(f"Deleting solution {solution_id}")

    try:
        solution_api.delete_solution(organization_id=organization_id, solution_id=solution_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Solution {solution_id} not found in organization {organization_id}.")
        return CommandResponse.fail()
    except ForbiddenException:
        logger.error(f"You are not allowed to delete the Solution : {solution_id}")
        return CommandResponse.fail()

    logger.info(f"Solutions {solution_id} of organization {organization_id} deleted.")

    return CommandResponse.success({"id": solution_id})