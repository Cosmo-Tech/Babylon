from logging import getLogger
from pprint import pformat
from typing import Optional

from click import command
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ......utils.api import get_api_file
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse
from ......utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **organization_api.update_organization**")
@timing_decorator
@pass_api_client
@require_deployment_key("organization_id", "organization_id")
@option("-i",
        "--organization-file",
        "organization_file",
        help="Your new Organization description file path",
        required=True)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def update(
    api_client: ApiClient,
    organization_file: str,
    organization_id: str,
    use_working_dir_file: Optional[bool] = False,
) -> CommandResponse:
    """Update an Organization by sending a JSON or YAML file to Cosmotech Api."""
    organization_api = OrganizationApi(api_client)

    converted_organization_content = get_api_file(
        api_file_path=organization_file,
        use_working_dir_file=use_working_dir_file,
    )
    if not converted_organization_content:
        logger.error("Can not get Organization definition, please check your Organization.YAML file")
        return CommandResponse.fail()

    try:
        retrieved_data = organization_api.update_organization(
            organization_id=organization_id,
            organization=converted_organization_content,
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} not found.")
        return CommandResponse.fail()
    except ForbiddenException:
        logger.error(f"You are not allowed to update the Organization : {organization_id}")
        return CommandResponse.fail()

    logger.debug(pformat(retrieved_data))
    logger.info(f"Updated organization with id: {retrieved_data['id']}")
    return CommandResponse.success(retrieved_data)
