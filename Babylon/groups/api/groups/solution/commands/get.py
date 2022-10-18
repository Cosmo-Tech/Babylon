import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from click import Path
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import underscore_to_camel
from ......utils.decorators import allow_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@allow_dry_run
@pass_solution_api
@timing_decorator
@argument("solution_id")
@require_deployment_key("organization_id", "organization_id")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get(
    solution_api: SolutionApi,
    solution_id: str,
    organization_id: str,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
    dry_run: bool = False,
):
    """Get the state of the solution in the API."""

    if dry_run:
        logger.info("DRY RUN - Would call solution_api.find_solution_by_id")
        retrieved_solution = {"Babylon": "<DRY RUN>"}
        return

    try:
        retrieved_solution = solution_api.find_solution_by_id(solution_id=solution_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Solution {solution_id} does not exists in organization {organization_id}.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return

    if fields:
        retrieved_solution = filter_api_response_item(retrieved_solution, fields.replace(' ','').split(","))
    if not output_file:
        logger.info(f"Solution {solution_id} details :")
        logger.info(pformat(retrieved_solution))
        return

    converted_content = convert_keys_case(retrieved_solution, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_content, _f, ensure_ascii=False)
        except TypeError:
            json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
    logger.debug(pformat(retrieved_solution))
    logger.info(f"Content was dumped on {output_file}")
