import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ....utils.api import convert_keys_case
from ....utils.api import filter_api_response_item
from ....utils.api import underscore_to_camel
from ....utils.decorators import describe_dry_run
from ....utils.decorators import require_deployment_key
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **organization_api.find_organization_by_id**")
@timing_decorator
@pass_api_client
@option("-o",
        "--output-file",
        "output_file",
        help="The path to the file where the new Organization content should be outputted (json-formatted)",
        type=Path())
@require_deployment_key("organization_id", "organization_id")
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get_current(
    api_client: ApiClient,
    organization_id: str,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
) -> CommandResponse:
    """Get the state of the current organization in the API."""
    organization_api = OrganizationApi(api_client)
    try:
        retrieved_organization = organization_api.find_organization_by_id(organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} not found.")
        return CommandResponse.fail()

    if fields:
        retrieved_organization = filter_api_response_item(retrieved_organization, fields.replace(" ", "").split(","))
    logger.debug(pformat(retrieved_organization))
    if not output_file:
        logger.info(f"Organization {organization_id} details : ")
        logger.info(pformat(retrieved_organization))
        return CommandResponse.success(retrieved_organization)

    converted_organization_content = convert_keys_case(retrieved_organization, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_organization_content.to_dict(), _f, ensure_ascii=False)
        except AttributeError:
            json.dump(converted_organization_content, _f, ensure_ascii=False)
        logger.info(f"Organization {organization_id} data was dumped on {output_file}.")
    return CommandResponse.success(retrieved_organization)