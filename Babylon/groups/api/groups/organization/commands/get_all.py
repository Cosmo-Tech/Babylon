import json
from logging import getLogger
from typing import Optional

from click import Path
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from rich import print
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_organization_api = make_pass_decorator(OrganizationApi)


@command()
@describe_dry_run("Would call **organization_api.find_all_organizations**")
@timing_decorator
@pass_organization_api
@option("-o",
        "--output-file",
        "output_file",
        help="The path to the file where the new Organization content should be outputted (json-formatted)",
        type=Path(writable=True))
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get_all(
    organization_api: OrganizationApi,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
):
    """Get all registered organization."""

    try:
        retrieved_organizations = organization_api.find_all_organizations()
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return

    logger.info(f"Found {len(retrieved_organizations)} organizations")
    logger.debug(retrieved_organizations)
    if fields:
        retrieved_organizations = filter_api_response(retrieved_organizations, fields.replace(" ", "").split(","))
    if not output_file:
        print(retrieved_organizations)
        return

    _organizations_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_organizations]
    with open(output_file, "w") as _file:
        try:
            json.dump([_ele.to_dict() for _ele in _organizations_to_dump], _file, ensure_ascii=False)
        except AttributeError:
            json.dump(_organizations_to_dump, _file, ensure_ascii=False)
    logger.info(f"Full content was dumped on {output_file}")
