from click import command

from cosmotech_api.api.organization_api import OrganizationApi
from click import make_pass_decorator
import logging
import pprint

logger = logging.getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)

@command()
@pass_organization_api
def get_all(organization_api: OrganizationApi):
    """Display all organization in API"""
    r = organization_api.find_all_organizations()
    logger.info(pprint.pformat(r))
