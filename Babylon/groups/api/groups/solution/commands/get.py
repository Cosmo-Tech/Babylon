import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.typing import QueryType

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@describe_dry_run("Would call **solution_api.find_solution_by_id** to get an solution details")
@pass_solution_api
@timing_decorator
@argument("solution-id", required=False, type=QueryType())
@require_deployment_key("organization_id", "organization_id")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where Connector details should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-i",
    "--solution-file",
    "solution_file",
    help="Your Solution description file path",
)
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def get(
    solution_api: SolutionApi,
    organization_id: str,
    solution_id: Optional[str] = None,
    fields: Optional[str] = None,
    output_file: Optional[str] = None,
    solution_file: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
):
    """Get the state of the solution in the API."""

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

        try:
            solution_id = converted_solution_content["id"]
        except KeyError:
            try:
                solution_id = converted_solution_content["solution_id"]
            except KeyError:
                logger.error("Can not get solution id, please check your file")
                return

    try:
        retrieved_solution = solution_api.find_solution_by_id(solution_id=solution_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Solution {solution_id} not found in organization {organization_id}.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return
    except ServiceException:
        logger.error(f"Organization with id {organization_id} not found.")
        return

    if fields:
        retrieved_solution = filter_api_response_item(retrieved_solution, fields.replace(" ", "").split(","))
    logger.debug(pformat(retrieved_solution))
    if not output_file:
        logger.info(f"Solution {solution_id} details :")
        logger.info(pformat(retrieved_solution))
        return

    converted_content = convert_keys_case(retrieved_solution, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
        except AttributeError:
            json.dump(converted_content, _f, ensure_ascii=False)
    logger.info(f"Content was dumped on {output_file}")
