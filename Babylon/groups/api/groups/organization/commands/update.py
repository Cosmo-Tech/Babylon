from logging import getLogger
from pprint import pformat
from typing import Optional

from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)


@command()
@allow_dry_run
@timing_decorator
@pass_organization_api
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
    organization_api: OrganizationApi,
    organization_file: str,
    organization_id: str,
    use_working_dir_file: Optional[bool] = False,
    dry_run: Optional[bool] = False,
):
    """Update an Organization by sending a JSON or YAML file to Cosmotech Api."""

    if dry_run:
        logger.info("DRY RUN - Would call organization_api.update_organization")
        return

    converted_organization_content = get_api_file(
        api_file_path=organization_file,
        use_working_dir_file=use_working_dir_file,
        logger=logger,
    )
    if not converted_organization_content:
        logger.error("Can not get Organization definition, please check your Organization.YAML file")
        return

    try:
        retrieved_data = organization_api.update_organization(
            organization_id=organization_id,
            organization=converted_organization_content,
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} does not exists.")
        return
    except ForbiddenException:
        logger.error(f"You are not allowed to update the Organization : {organization_id}")
        return

    logger.debug(pformat(retrieved_data))
    logger.info(f"Updated organization with id: {retrieved_data['id']}")
