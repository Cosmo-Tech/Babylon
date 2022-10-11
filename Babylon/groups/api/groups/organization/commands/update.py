from logging import getLogger
from pprint import pformat

from cosmotech_api.exceptions import NotFoundException, UnauthorizedException
from click import argument, command, make_pass_decorator, option
from cosmotech_api.api.organization_api import OrganizationApi

from Babylon.utils.api import get_api_file
from Babylon.utils.decorators import allow_dry_run, timing_decorator, require_deployment_key

logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)

@command()
@allow_dry_run
@timing_decorator
@pass_organization_api
@require_deployment_key("organization_id", "organization_id")
@argument("organization_file")
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
    use_working_dir_file: bool = False,
    dry_run: bool = False,
):
    """Update an Organization by sending a JSON or YAML file to Cosmotech Api."""

    converted_organization_content = get_api_file(
            api_file_path=organization_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
    if not converted_organization_content:
        logger.error("Error : can not get Organization definition, please check your Organization.YAML file")
        return

    if dry_run:
        logger.info("DRY RUN - Would call organization_api.update_organization")
        retrieved_data = converted_organization_content
        retrieved_data["id"] = "<DRY RUN>"
        return

    try:
        retrieved_data = organization_api.update_organization(
            organization_id=organization_id,
            organization=converted_organization_content,
        )
    except UnauthorizedException :
        logger.error("Unauthorized access to the cosmotech api")
    except  NotFoundException :
        logger.error("Organization with id %s does not exists.", organization_id)

    logger.debug(pformat(retrieved_data))
    logger.info("Updated organization with id: %s", retrieved_data['id'])
