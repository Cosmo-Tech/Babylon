import json
import logging
from pprint import pformat
from typing import Optional

import cosmotech_api
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.solution_api import SolutionApi

from ......utils.api import convert_keys_case
from ......utils.api import underscore_to_camel
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@pass_solution_api
@require_deployment_key("organization_id", "organization_id")
@option("-o", "--output_file", "output_file", help="File to which content should be outputed (json-formatted)")
@timing_decorator
def get_all_ids(solution_api: SolutionApi, organization_id: str, output_file: Optional[str] = None):
    """Get the state of the solution in the API"""
    try:
        r = solution_api.find_all_solutions(organization_id=organization_id)
        logger.debug(pformat(r))
        if output_file is not None:
            _sols = []
            for _s in r:
                converted_content = convert_keys_case(_s.to_dict(), underscore_to_camel)
                _sols.append(converted_content)
            with open(output_file, "w") as _f:
                json.dump(_sols, _f, ensure_ascii=False)
            logger.info(f"Full content was dumped on {output_file}")
        else:
            ids = dict({_s['id']: _s['name'] for _s in r})
            logger.info(pformat(ids, sort_dicts=False))
            logger.info(f"Found {len(ids)} solutions in organization {organization_id}")
    except cosmotech_api.exceptions.NotFoundException:
        logger.error(f"Organization {organization_id} was not found.")
    except cosmotech_api.exceptions.UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
