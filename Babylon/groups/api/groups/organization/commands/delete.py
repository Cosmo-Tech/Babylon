from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import describe_dry_run
from ......utils.decorators import timing_decorator
from ......utils.interactive import confirm_deletion

logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)


@command()
@describe_dry_run("Would call **organization_api.unregister_organization**")
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
    force_validation: Optional[bool] = False,
    use_working_dir_file: Optional[bool] = False,
) -> Optional[str]:
    """Delete organization via Cosmotech APi."""

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

        organization_id = converted_organization_content.get("id") or converted_organization_content.get(
            "organization_id")
        if not organization_id:
            logger.error("Can not get organization id, please check your file")
            return

    try:
        organization_api.find_organization_by_id(organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} not found.")
        return

    if not force_validation and not confirm_deletion("organization", organization_id):
        return

    logger.info(f"Deleting organization {organization_id}")

    try:
        organization_api.unregister_organization(organization_id)
        logger.info(f"Organization with id {organization_id} deleted.")
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} not found.")
        return
    except ForbiddenException:
        logger.error(f"You are not allowed to delete the Organization : {organization_id}")
        return

    return organization_id
