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

from ....utils.api import convert_keys_case
from ....utils.api import filter_api_response
from ....utils.api import underscore_to_camel
from ....utils.decorators import describe_dry_run
from ....utils.decorators import require_deployment_key
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **solution_api.find_all_solutions** to get all registered solution")
@timing_decorator
@pass_api_client
@require_deployment_key("organization_id", "organization_id")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where Solutions should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get_all(
    api_client: ApiClient,
    organization_id: str,
    fields: Optional[str] = None,
    output_file: Optional[str] = None,
) -> CommandResponse:
    """Get all registered solutions."""
    solution_api = SolutionApi(api_client)
    try:
        retrieved_solutions = solution_api.find_all_solutions(organization_id)
    except NotFoundException:
        logger.error(f"Organization {organization_id} was not found.")
        return CommandResponse.fail()
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id {organization_id} not found.")
        return CommandResponse.fail()

    if fields:
        retrieved_solutions = filter_api_response(retrieved_solutions, fields.replace(" ", "").split(","))
    logger.info(f"Found {len(retrieved_solutions)} solutions")
    logger.debug(pformat(retrieved_solutions))
    if not output_file:
        logger.info(pformat(retrieved_solutions, sort_dicts=False))
        return CommandResponse.success({"solutions": retrieved_solutions})

    _solutions_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_solutions]
    with open(output_file, "w") as _file:
        try:
            json.dump([_ele.to_dict() for _ele in _solutions_to_dump], _file, ensure_ascii=False)
        except AttributeError:
            json.dump(_solutions_to_dump, _file, ensure_ascii=False)
    logger.info("Full content was dumped on %s.", output_file)
    return CommandResponse.success({"solutions": retrieved_solutions})
