import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse
from ......utils.credentials import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **solution_api.find_solution_by_id** get the current solution details")
@pass_api_client
@timing_decorator
@require_deployment_key("solution_id", "solution_id")
@require_deployment_key("organization_id", "organization_id")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where Connector details should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get_current(
    api_client: ApiClient,
    solution_id: str,
    organization_id: str,
    fields: Optional[str] = None,
    output_file: Optional[str] = None,
) -> CommandResponse:
    """Get the state of the solution in the API."""
    solution_api = SolutionApi(api_client)
    try:
        retrieved_solution = solution_api.find_solution_by_id(solution_id=solution_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Solution {solution_id} not found in organization {organization_id}.")
        return CommandResponse.fail()
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id {organization_id} not found.")
        return CommandResponse.fail()

    if fields:
        retrieved_solution = filter_api_response_item(retrieved_solution, fields.replace(" ", "").split(","))
    logger.debug(pformat(retrieved_solution))
    if not output_file:
        logger.info(f"Solution {solution_id} details :")
        logger.info(pformat(retrieved_solution))
        return CommandResponse.success(retrieved_solution)

    converted_content = convert_keys_case(retrieved_solution, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
        except AttributeError:
            json.dump(converted_content, _f, ensure_ascii=False)
    logger.info(f"Content was dumped on {output_file}")
    return CommandResponse.success(retrieved_solution)
