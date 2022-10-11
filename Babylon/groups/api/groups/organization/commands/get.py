import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from cosmotech_api.exceptions import NotFoundException, UnauthorizedException
from click import argument, command, make_pass_decorator, option
from cosmotech_api.api.organization_api import OrganizationApi

from Babylon.utils.api import convert_keys_case, underscore_to_camel, filter_api_response_item
from Babylon.utils.decorators import allow_dry_run, timing_decorator

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
@argument("organization_id", type=str)
@option(
    "-f",
    "--fields",
    "fields",
    required=False,
    type=str,
    help="Fields witch will be keep in response data, by default all",
)
def get(
    organization_api: OrganizationApi,
    organization_id: str,
    output_file: Optional[str] = None,
    fields: str = None,
    dry_run: bool = False,
):
    """Get the state of an specific organization in the API."""

    if dry_run:
        logger.info("DRY RUN - Would call organization_api.find_organization_by_id")
        retrieved_organization = {"Babylon": "<DRY RUN>"}
        return

    try:
        retrieved_organization = organization_api.find_organization_by_id(
            organization_id
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error("Organization with id %s does not exist.", organization_id)
        return

    if fields:
        retrieved_organization = filter_api_response_item(
            retrieved_organization, fields.split(",")
        )
    if not output_file:
        logger.info("Organization %s details :", organization_id)
        logger.info(pformat(retrieved_organization))
    else:
        converted_content = convert_keys_case(
            retrieved_organization.to_dict(), underscore_to_camel
        )
        with open(output_file, "w") as _file:
            json.dump(converted_content, _file, ensure_ascii=False)
        logger.info("Organization %s data was dumped on %s", organization_id, output_file)

