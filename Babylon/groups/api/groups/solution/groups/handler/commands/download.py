from logging import getLogger

from click import Choice
from click import command
from click import option
from cosmotech_api.api.solution_api import SolutionApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ........utils.decorators import describe_dry_run
from ........utils.decorators import require_deployment_key
from ........utils.decorators import timing_decorator
from ........utils.response import CommandResponse
from ........utils.credentials import pass_api_client

logger = getLogger("Babylon")


@command()
@timing_decorator
@pass_api_client
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
@describe_dry_run("Would call **solution_api.download_run_template_handler** to download a solution handler zip")
def download(
    api_client: ApiClient,
    organization_id: str,
    solution_id: str,
    handler_id: str,
    run_template_id: str,
) -> CommandResponse:
    """Download a solution handler zip."""
    solution_api = SolutionApi(api_client)

    logger.info(f"Downloading {handler_id} handler from solution {solution_id}")
    try:
        response = solution_api.download_run_template_handler(
            organization_id=organization_id,
            solution_id=solution_id,
            run_template_id=run_template_id,
            handler_id=handler_id,
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

    if not response:
        logger.error("No retrieved handler")
        return CommandResponse.fail()

    with open(run_template_id + ".zip", "wb") as _f:
        _f.write(response.read())

    logger.debug(response)
    logger.info(f"{handler_id} handler downloaded from solution {solution_id} successfully")
    return CommandResponse.success({"id": handler_id, "file": f"{run_template_id}.zip"})
