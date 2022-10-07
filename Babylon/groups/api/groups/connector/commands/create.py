from logging import getLogger
from pprint import pformat
from typing import Optional

from click import argument, command, make_pass_decorator, option, Choice
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.decorators import allow_dry_run, pass_environment, timing_decorator
from ......utils.environment import Environment

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)


@command()
@allow_dry_run
@timing_decorator
@pass_connector_api
@pass_environment
@argument("connector_file", type=str, required=False)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
@option(
    "-t",
    "--type",
    "connector_type",
    required=True,
    type=Choice(["ADT", "STORAGE"], case_sensitive=True),
    help="Connector type, allowed values : [ADT, STORAGE]",
)
@option(
    "-n",
    "--name",
    "connector_name",
    required=True,
    type=str,
    help="New connector name",
)
@option(
    "-v",
    "--version",
    "connector_version",
    required=True,
    type=str,
    help="New connector version",
)
def create(
    env: Environment,
    connector_api: ConnectorApi,
    connector_type: str,
    connector_name: str,
    connector_version: str,
    connector_file: Optional[str] = None,
    use_working_dir_file: bool = False,
    dry_run: bool = False,
):
    """Register new connector by sending a JSON or YAML file to the API."""

    converted_connector_content = get_api_file(
        api_file_path=connector_file
        if connector_file
        else f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Connector.{connector_type}.yaml",
        use_working_dir_file=use_working_dir_file if connector_file else False,
        logger=logger,
    )

    if (converted_connector_content) is not None:
        try:

            if not dry_run:
                retrieved_connector = connector_api.register_connector(
                    connector=converted_connector_content
                )
                converted_connector_content["name"] = connector_name
                converted_connector_content["key"] = "".join(connector_name.split(" "))
                converted_connector_content["version"] = connector_version

                if connector_type == "ADT":
                    env.configuration.set_deploy_var(
                        "adt_connector_id", retrieved_connector["id"]
                    )
                elif connector_type == "STORAGE":
                    env.configuration.set_deploy_var(
                        "azure_storage_connector_id", retrieved_connector["id"]
                    )
            else:
                logger.info("DRY RUN - Would call connector_api.create_connector")
                retrieved_connector = converted_connector_content
                retrieved_connector["id"] = "<DRY RUN>"

            logger.debug(pformat(retrieved_connector))
            logger.info(
                f"Created new {connector_type} Connector with id: {retrieved_connector['id']}"
            )

        except UnauthorizedException:
            logger.error("Unauthorized access to the cosmotech api")

    else:
        logger.error(
            "Error : can not get correct Connector definition, please check your Connector.YAML file"
        )
