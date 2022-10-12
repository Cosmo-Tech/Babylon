import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import UnauthorizedException

from Babylon.utils.api import convert_keys_case
from Babylon.utils.api import filter_api_response
from Babylon.utils.api import underscore_to_camel
from Babylon.utils.decorators import allow_dry_run
from Babylon.utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)


@command()
@allow_dry_run
@timing_decorator
@pass_organization_api
@option(
    "-o",
    "--output_file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
)
@option(
    "-f",
    "--fields",
    "fields",
    required=False,
    type=str,
    help="Fields witch will be keep in response data, by default all",
)
def get_all(
    organization_api: OrganizationApi,
    output_file: Optional[str] = None,
    fields: str = None,
    dry_run: bool = False,
):
    """Get all registered organization."""

    if dry_run:
        retrieved_organizations = [{"Babylon": "<DRY RUN>"}]
        logger.info("DRY RUN - Would call organization_api.find_all_organizations")
        logger.info(pformat(retrieved_organizations))
        return

    try:
        retrieved_organizations = organization_api.find_all_organizations()
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return

    if fields:
        retrieved_organizations = filter_api_response(retrieved_organizations, fields.split(","))
        logger.info("Found %s organizations", len(retrieved_organizations))
    if output_file:
        _organizations_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_organizations]
        with open(output_file, "w") as _file:
            json.dump(_organizations_to_dump, _file, ensure_ascii=False)
        logger.info("Full content was dumped on %s", output_file)
        return
    logger.info(pformat(retrieved_organizations))
