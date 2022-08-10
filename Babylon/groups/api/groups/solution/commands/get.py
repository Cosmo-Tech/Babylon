import logging
from pprint import pformat
from typing import Optional
import json

import cosmotech_api
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from ......utils.api import convert_keys_case, underscore_to_camel

from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@pass_solution_api
@require_deployment_key("organization_id", "organization_id")
@require_deployment_key("solution_id", "solution_id")
@option("-o", "--output_file", "output_file", help="File to which content should be outputed (json-formatted)")
@timing_decorator
def get(solution_api: SolutionApi, solution_id: str, organization_id: str, output_file: Optional[str] = None):
    """Get the state of the solution in the API"""
    try:
        r = solution_api.find_solution_by_id(solution_id=solution_id, organization_id=organization_id)
        if output_file is not None:
            converted_content = convert_keys_case(r.to_dict(), underscore_to_camel)
            with open(output_file, "w") as _f:
                json.dump(converted_content, _f, ensure_ascii=False)
            logger.debug(pformat(r))
            logger.info(f"Content was dumped on {output_file}")
        else:
            logger.info(pformat(r))
    except cosmotech_api.exceptions.NotFoundException as _e:
        logger.error(f"Solution {solution_id} does not exists in organization {organization_id}.")
    except cosmotech_api.exceptions.UnauthorizedException as _e:
        logger.error("Unauthorized access to the cosmotech api")
