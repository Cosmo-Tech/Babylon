import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)


@command()
@describe_dry_run("Would call **organization_api.find_organization_by_id**")
@timing_decorator
@pass_organization_api
@option("-o",
        "--output-file",
        "output_file",
        help="The path to the file where the new Organization content should be outputted (json-formatted)",
        type=Path())
@require_deployment_key("organization_id")
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get_current(
    organization_api: OrganizationApi,
    organization_id: str,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
):
    """Get the state of the current organization in the API."""

    try:
        retrieved_organization = organization_api.find_organization_by_id(organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} not found.")
        return

    if fields:
        retrieved_organization = filter_api_response_item(retrieved_organization, fields.replace(" ", "").split(","))
    logger.debug(pformat(retrieved_organization))
    if not output_file:
        logger.info(f"Organization {organization_id} details : ")
        logger.info(pformat(retrieved_organization))
        return

    converted_organization_content = convert_keys_case(retrieved_organization, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_organization_content.to_dict(), _f, ensure_ascii=False)
        except AttributeError:
            json.dump(converted_organization_content, _f, ensure_ascii=False)
        logger.info(f"Organization {organization_id} data was dumped on {output_file}.")
