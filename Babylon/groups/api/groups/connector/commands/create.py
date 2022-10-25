import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Choice
from click import Path
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import UnauthorizedException

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.api import convert_keys_case
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import allow_dry_run
from ......utils.decorators import pass_environment
from ......utils.decorators import timing_decorator
from ......utils.environment import Environment

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)


@command()
@allow_dry_run
@timing_decorator
@pass_connector_api
@pass_environment
@option("-f", "--connector-file", "connector_file", type=str, help="Your custom Connector description file path")
@option("-t",
        "--type",
        "connector_type",
        required=True,
        type=Choice(["ADT", "STORAGE"], case_sensitive=False),
        help="Connector type, allowed values : [ADT, STORAGE]")
@option("-s",
        "--select",
        "select",
        type=bool,
        help="Select this new Connector as one of babylon context Connectors ?",
        default=True)
@option("-o",
        "--output-file",
        "output_file",
        help="The path to the file where the new Connector content should be outputted (json-formatted)",
        type=Path())
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the Connector file path be relative to Babylon working directory ?")
@argument("connector-name", required=True)
@option("-v", "--version", "connector_version", required=True, help="Version of the Connector")
def create(
    env: Environment,
    connector_api: ConnectorApi,
    select: bool,
    connector_type: str,
    connector_name: str,
    connector_version: str,
    dry_run: Optional[str] = False,
    output_file: Optional[str] = None,
    connector_file: Optional[str] = None,
    use_working_dir_file: Optional[str] = False,
):
    """Register a new Connector by sending a JSON or YAML file to the API."""

    if dry_run:
        logger.info("DRY RUN - Would call connector_api.create_connector to register a new Connector")
        return

    connector_type = connector_type.upper()
    converted_connector_content = get_api_file(
        api_file_path=connector_file
        if connector_file else f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Connector.{connector_type}.yaml",
        use_working_dir_file=use_working_dir_file if connector_file else False,
        logger=logger,
    )
    if not converted_connector_content:
        logger.error("Error : can not get correct Connector definition, please check your Connector.YAML file")
        return

    converted_connector_content["name"] = connector_name
    converted_connector_content["version"] = connector_version
    if "key" not in converted_connector_content or not converted_connector_content["key"]:
        converted_connector_content["key"] = connector_name.replace(" ", "")
    if "description" not in converted_connector_content or not converted_connector_content["description"]:
        converted_connector_content["description"] = connector_name

    try:
        retrieved_connector = connector_api.register_connector(connector=converted_connector_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return

    if select:
        env.configuration.set_deploy_var(f"{connector_type.lower()}_connector_id", retrieved_connector["id"])

    logger.debug(pformat(retrieved_connector))
    logger.info("Created new %s Connector with id: %s", connector_type, retrieved_connector['id'])

    if output_file:
        converted_connector_content = convert_keys_case(retrieved_connector, underscore_to_camel)
        with open(output_file, "w") as _f:
            try:
                json.dump(converted_connector_content, _f, ensure_ascii=False)
            except TypeError:
                json.dump(converted_connector_content.to_dict(), _f, ensure_ascii=False)
        logger.info(f"Content was dumped on {output_file}")
