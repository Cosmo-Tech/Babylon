from logging import getLogger
from typing import Optional

from click import Choice
from click import Path
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ........utils.decorators import allow_dry_run
from ........utils.decorators import pass_environment
from ........utils.decorators import require_deployment_key
from ........utils.decorators import timing_decorator
from ........utils.environment import Environment

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@allow_dry_run
@timing_decorator
@pass_solution_api
@pass_environment
@argument("handler-path", type=Path())
@option(
    "-t",
    "--run-template",
    "run_template_id",
    help="The run Template identifier",
    required=True,
)
@option(
    "-h",
    "--handler-type",
    "handler_id",
    type=Choice(
        [
            "parameters_handler",
            "validator",
            "prerun",
            "engine",
            "postrun",
            "scenariodata_transform",
        ],
        case_sensitive=False,
    ),
    help="Handler type, allowed values\
        :[parameters_handler, validator,\
            prerun, engine, postrun, scenariodata_transform]",
)
@require_deployment_key("organization_id", "organization_id")
@require_deployment_key("solution_id", "solution_id")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def upload(
    env: Environment,
    solution_api: SolutionApi,
    organization_id: str,
    solution_id: str,
    handler_path: str,
    handler_id: str,
    run_template_id: str,
    use_working_dir_file: Optional[bool] = False,
    dry_run: Optional[bool] = False,
) -> Optional[str]:
    """Send a JSON or YAML file to the API to create an solution."""

    try:
        handler = open(handler_path, 'rb')
        _ = solution_api.upload_run_template_handler(
            organization_id=organization_id,
            solution_id=solution_id,
            run_template_id=run_template_id,
            handler_id=handler_id,
            body=handler,
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} not found.")
        return
    except ServiceException:
        logger.error(f"Organization with id {organization_id} and or Solution {solution_id} not found.")
        return
    logger.info("Created new solution with ")
