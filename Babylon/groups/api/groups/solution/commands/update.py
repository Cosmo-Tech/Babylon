from logging import getLogger
from pprint import pformat
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
from ......utils.typing import QueryType
from ......utils.response import CommandResponse

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@describe_dry_run("Would call **solution_api.create_solution** to update an solution")
@timing_decorator
@pass_solution_api
@argument("solution-id", required=False, type=QueryType())
@require_deployment_key("simulator_version", "simulator_version")
@require_deployment_key("simulator_repository", "simulator_repository")
@require_deployment_key("organization_id", "organization_id")
@require_deployment_key("solution_id", "solution_id")
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
    help="Your custom Solution description file path",
)
def update(
    solution_api: SolutionApi,
    organization_id: str,
    solution_id: str,
    simulator_version: str,
    simulator_repository: str,
    solution_file: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
) -> CommandResponse:
    """Send a JSON or YAML file to the API to update a solution."""

    converted_solution_content = dict()

    if solution_file:
        converted_solution_content = get_api_file(api_file_path=solution_file,
                                                  use_working_dir_file=use_working_dir_file)

        if not converted_solution_content:
            logger.error("Can not get correct connector definition, please check your Solution.YAML file")
            return CommandResponse.fail()

        try:
            del converted_solution_content["id"]
        except Exception:
            ...

    converted_solution_content["version"] = simulator_version
    converted_solution_content["repository"] = simulator_repository

    try:
        retrieved_solution = solution_api.update_solution(solution_id=solution_id,
                                                          organization_id=organization_id,
                                                          solution=converted_solution_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Solution {solution_id} not found in organization {organization_id}.")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id {organization_id} not found.")
        return CommandResponse.fail()
    except ForbiddenException:
        logger.error(f"You are not allowed to update the solution : {solution_id}")
        return CommandResponse.fail()

    logger.info(f"Updated solution: {solution_id}  with \n"
                f" - repository: {retrieved_solution['repository']}\n"
                f" - version: {retrieved_solution['version']}")
    logger.debug(pformat(retrieved_solution))
    return CommandResponse(data=retrieved_solution)
