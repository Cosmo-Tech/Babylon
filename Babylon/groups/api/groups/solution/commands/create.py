import logging
from pprint import pformat

import cosmotech_api
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.solution_api import SolutionApi

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@pass_solution_api
@require_deployment_key("organization_id", "organization_id")
@argument("solution_file")
@option("-e", "--use-solution-file", "use_solution_file", is_flag=True,
        help="Should the path be in the solution ?")
@allow_dry_run
@timing_decorator
def create(solution_api: SolutionApi,
           organization_id: str,
           solution_file: str,
           use_solution_file: bool = False,
           dry_run: bool = False):
    """Send a JSON or YAML file to the API to create a solution"""

    if (converted_solution_content := get_api_file(api_file_path=solution_file,
                                                   use_working_dir_file=use_solution_file,
                                                   logger=logger)) is not None:
        try:
            if not dry_run:
                r = solution_api.create_solution(organization_id=organization_id, solution=converted_solution_content)
            else:
                logger.info("DRY RUN - Would call solution_api.create_solution")
                r = converted_solution_content
                r['id'] = "<DRY RUN>"
            logger.debug(pformat(r))
            logger.info(f"Created new solution with id: {r['id']}")
        except cosmotech_api.exceptions.UnauthorizedException as _e:
            logger.error("Unauthorized access to the cosmotech api")
