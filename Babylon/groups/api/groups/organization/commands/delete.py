from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import confirm
from click import make_pass_decorator
from click import option
from click import prompt
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)


@command()
@allow_dry_run
@timing_decorator
@pass_organization_api
@argument(
    "organization_id",
    required=False,
)
@option(
    "-i",
    "--organization-file",
    "organization_file",
    help="In case the organization id is retrieved from a file",
)
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def delete(
    organization_api: OrganizationApi,
    organization_id: str,
    organization_file: Optional[str] = None,
    dry_run: Optional[bool] = False,
    force_validation: Optional[bool] = False,
    use_working_dir_file: Optional[bool] = False,
) -> Optional[str]:
    """Delete organization via Cosmotech APi."""

    if dry_run:
        logger.info("DRY RUN - Would call organization_api.unregister_organization")
        return

    if not organization_id:
        if not organization_file:
            logger.error("No id passed as argument or option \n"
                         "Use -i option to pass an json or yaml file containing an organization id.")
            return

        converted_organization_content = get_api_file(
            api_file_path=organization_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
        if not converted_organization_content:
            logger.error("Can not get organization definition, please check your file")
            return

        try:
            organization_id = converted_organization_content["id"]
        except KeyError:
            try:
                organization_id = converted_organization_content["organization_id"]
            except KeyError:
                logger.error("Can not get organization id, please check your file")
                return

    try:
        organization_api.find_organization_by_id(organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} does not exists.")
        return

    if not force_validation:
        if not confirm(f"You are trying to delete organization {organization_id} \nDo you want to continue?"):
            logger.info("Organization deletion aborted.")
            return

        confirm_organization_id = prompt("Confirm organization id ")
        if confirm_organization_id != organization_id:
            logger.error("The Organization id you have type didn't mach with Organization you are trying to delete id")
            return

    logger.info(f"Deleting organization {organization_id}")

    try:
        organization_api.unregister_organization(organization_id)
        logger.info(f"Organization with id {organization_id} deleted.")
    except UnauthorizedException:
        logger.error(f"Unauthorized access to the cosmotech api")
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} does not exists.")
    except ForbiddenException:
        logger.error(f"You are not allowed to delete the Organization : {organization_id}")

    return organization_id
