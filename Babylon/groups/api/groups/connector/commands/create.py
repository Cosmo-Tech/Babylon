from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Choice
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import UnauthorizedException

from Babylon.utils import TEMPLATE_FOLDER_PATH
from Babylon.utils.api import get_api_file
from Babylon.utils.decorators import allow_dry_run
from Babylon.utils.decorators import pass_environment
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)


@command()
@allow_dry_run
@timing_decorator
@pass_connector_api
@pass_environment
@argument("connector_file", type=str, required=False)
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the path be relative to the working directory ?")
@option("-t",
        "--type",
        "connector_type",
        required=True,
        type=Choice(["ADT", "STORAGE"], case_sensitive=False),
        help="Connector type, allowed values : [ADT, STORAGE]")
@option("-n", "--name", "connector_name", required=True, type=str, help="New connector name")
@option("-v", "--version", "connector_version", required=True, type=str, help="New connector version")
def create(env: Environment,
           connector_api: ConnectorApi,
           connector_type: str,
           connector_name: str,
           connector_version: str,
           connector_file: Optional[str] = None,
           use_working_dir_file: bool = False,
           dry_run: bool = False):
    """Register new connector by sending a JSON or YAML file to the API."""

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

    if dry_run:
        logger.info("DRY RUN - Would call connector_api.create_connector")
        retrieved_connector = converted_connector_content
        retrieved_connector["id"] = "<DRY RUN>"
        return

    converted_connector_content["name"] = connector_name
    converted_connector_content["key"] = connector_name.replace(" ", "")
    converted_connector_content["version"] = connector_version
    try:
        retrieved_connector = connector_api.register_connector(connector=converted_connector_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    env.configuration.set_deploy_var(f"{connector_type.lower()}_connector_id", retrieved_connector["id"])
    logger.debug(pformat(retrieved_connector))
    logger.info("Created new %s Connector with id: %s", connector_type, retrieved_connector['id'])
