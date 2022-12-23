from logging import getLogger
from typing import Optional

from click import Choice
from click import Path
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import ApiException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ........utils.decorators import describe_dry_run
from ........utils.decorators import require_deployment_key
from ........utils.decorators import timing_decorator
from ........utils.response import CommandResponse

logger = getLogger("Babylon")

pass_solution_api = make_pass_decorator(SolutionApi)


@command()
@timing_decorator
@pass_solution_api
@argument("handler-path", type=Path())
@option("-o", "--override", "override", is_flag=True)
@option(
    "-r",
    "--run-template",
    "run_template_id",
    help="The run Template identifier",
    required=True,
)
@option(
    "-t",
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
    required=True,
    help="Handler type",
)
@require_deployment_key("organization_id", "organization_id")
@require_deployment_key("solution_id", "solution_id")
@describe_dry_run("Would call **solution_api.upload_run_template_handler** to upload a solution handler zip")
def upload(
    solution_api: SolutionApi,
    organization_id: str,
    solution_id: str,
    handler_path: str,
    handler_id: Path,
    run_template_id: str,
    override: Optional[bool] = False,
) -> CommandResponse:
    """Upload a solution handler zip."""

    if not handler_path.endswith(".zip"):
        logger.error(f"{handler_path} is not a zip archive")
        return CommandResponse.fail()

    try:
        handler = open(handler_path, 'rb')
    except IOError:
        logger.error(f"{handler_path} : file not found")
        return CommandResponse.fail()

    logger.info(f"Uploading {handler_id} handler to solution {solution_id}")
    try:
        response = solution_api.upload_run_template_handler(
            organization_id=organization_id,
            solution_id=solution_id,
            run_template_id=run_template_id,
            handler_id=handler_id,
            body=handler,
            overwrite=override,
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} not found.")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id {organization_id} and or Solution {solution_id} not found.")
        return CommandResponse.fail()
    except ApiException as e:
        logger.error(f"An error occurred : { e.body}")
        return CommandResponse.fail()

    logger.debug(response)
    logger.info(f"{handler_id} handler uploaded to solution {solution_id} successfully")
    return CommandResponse(data={"id": handler_id})
