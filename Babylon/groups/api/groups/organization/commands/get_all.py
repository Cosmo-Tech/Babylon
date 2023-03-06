import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse
from ......utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **organization_api.find_all_organizations**")
@timing_decorator
@pass_api_client
@option("-o",
        "--output-file",
        "output_file",
        help="The path to the file where the new Organization content should be outputted (json-formatted)",
        type=Path())
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get_all(
    api_client: ApiClient,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
) -> CommandResponse:
    """Get all registered organization."""
    organization_api = OrganizationApi(api_client)
    try:
        retrieved_organizations = organization_api.find_all_organizations()
    except UnauthorizedException as e:
        logger.error("Unauthorized access to the cosmotech api")
        logger.error(e)
        return CommandResponse.fail()

    logger.info(f"Found {len(retrieved_organizations)} organizations")
    logger.debug(pformat(retrieved_organizations))
    if fields:
        retrieved_organizations = filter_api_response(retrieved_organizations, fields.replace(" ", "").split(","))
    _organizations_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_organizations]
    data = [_ele.to_dict() for _ele in _organizations_to_dump]
    if not output_file:
        logger.info(pformat(retrieved_organizations))
        return CommandResponse.success({"organizations": data})

    with open(output_file, "w") as _file:
        try:
            json.dump(data, _file, ensure_ascii=False)
        except AttributeError:
            json.dump(_organizations_to_dump, _file, ensure_ascii=False)
    logger.info(f"Full content was dumped on {output_file}")
    return CommandResponse.success({"organizations": data})
