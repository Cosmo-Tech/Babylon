from logging import getLogger

from cosmotech_api.exceptions import NotFoundException, UnauthorizedException
from click import argument, command, confirm, make_pass_decorator, prompt
from cosmotech_api.api.organization_api import OrganizationApi

from Babylon.utils.decorators import allow_dry_run, timing_decorator


logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)

@command()
@allow_dry_run
@timing_decorator
@pass_organization_api
@argument("organization_id", type=str)
def delete(
    organization_api: OrganizationApi,
    organization_id: str,
    dry_run: bool = False,
):
    """Delete organization via Cosmotech APi."""

    if dry_run:
        logger.info("DRY RUN - Would call organization_api.unregister_organization")
        return

    try:
        organization_api.find_organization_by_id(organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error("Organization with id %s does not exists.",organization_id)
        return

    if not confirm("You are trying to delete organization {organization_id} \nDo you want to continue?"):
        logger.info("Organization deletion aborted.")
        return

    confirm_organization_id = prompt("Confirm organization id ")
    if confirm_organization_id != organization_id:
        logger.error("The Organization id you have type didn't mach with Organization you are trying to delete id")
        return

    try:
        organization_api.unregister_organization(organization_id)
        logger.info("Organization with id %s deleted.", organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
    except NotFoundException:
        logger.error("Organization with id %s does not exists.", organization_id)
