import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import underscore_to_camel
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
def get_current(
    organization_api: OrganizationApi,
    organization_id: str,
    output_file: Optional[str] = None,
    fields: str = None,
    dry_run: bool = False,
):
    """Get the state of current configuration organization in the API."""

    if dry_run:
        logger.info("DRY RUN - Would call organization_api.find_organization_by_id")
        retrieved_organization = {"Babylon": "<DRY RUN>"}
        return

    try:
        retrieved_organization = organization_api.find_organization_by_id(organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error("Organization with id {organization_id} does not exist.")
        return

    if fields:
        retrieved_organization = filter_api_response_item(retrieved_organization, fields.split(","))
    if output_file:
        converted_content = convert_keys_case(retrieved_organization.to_dict(), underscore_to_camel)
        with open(output_file, "w") as _file:
            json.dump(converted_content, _file, ensure_ascii=False)
        logger.info("Organization {organization_id} data was dumped on {output_file}.")
        return
    logger.info(f"Organization {organization_id} details :")
    logger.info(pformat(retrieved_organization))
