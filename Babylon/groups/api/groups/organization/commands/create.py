import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import argument
from click import command
from click import option
from cosmotech_api.api.organization_api import OrganizationApi
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.api import convert_keys_case
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import timing_decorator
from ......utils.environment import Environment
from ......utils.typing import QueryType
from ......utils.response import CommandResponse
from ......utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **organization_api.create_organization** to register a new Organization")
@timing_decorator
@pass_api_client
@option("-i", "--organization-file", "organization_file", help="Your custom Organization description file path")
@option("-s",
        "--select",
        "select",
        type=bool,
        help="Select this new Organization as one of babylon context Organizations ?",
        default=True)
@option("-o",
        "--output-file",
        "output_file",
        help="The path to the file where the new Organization content should be outputted (json-formatted)",
        type=Path())
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the Organization file path be relative to Babylon working directory ?")
@argument("organization-name", type=QueryType())
def create(
    api_client: ApiClient,
    select: bool,
    organization_name: str,
    output_file: Optional[str] = None,
    organization_file: Optional[str] = None,
    use_working_dir_file: bool = False,
) -> CommandResponse:
    """Register new organization by sending a JSON or YAML file"""
    env = Environment()
    organization_api = OrganizationApi(api_client)
    converted_organization_content = get_api_file(
        api_file_path=organization_file or f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Organization.yaml",
        use_working_dir_file=use_working_dir_file if organization_file else False)

    if converted_organization_content is None:
        logger.error("Can not get Organization definition, please check your Organization.YAML file")
        return CommandResponse.fail()

    converted_organization_content["name"] = organization_name

    try:
        retrieved_organization = organization_api.register_organization(organization=converted_organization_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()

    if select:
        env.configuration.set_deploy_var(
            "organization_id",
            retrieved_organization["id"],
        )  # May return environnement error
    logger.debug(pformat(retrieved_organization))
    logger.info(f"Created new organization with id: {retrieved_organization['id']}")

    if output_file:
        converted_organization_content = convert_keys_case(retrieved_organization, underscore_to_camel)
        with open(output_file, "w") as _f:
            try:
                json.dump(converted_organization_content, _f, ensure_ascii=False)
            except TypeError:
                json.dump(converted_organization_content.to_dict(), _f, ensure_ascii=False)
        logger.info(f"Content was dumped on {output_file}")

    return CommandResponse.success(retrieved_organization)
