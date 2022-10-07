from logging import getLogger
from pprint import pformat

from click import argument, command, make_pass_decorator, option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run, timing_decorator

logger = getLogger("Babylon")

pass_connector_api = make_pass_decorator(ConnectorApi)


@command()
@allow_dry_run
@timing_decorator
@pass_connector_api
@argument("connector_file", type=str)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def create(
    connector_api: ConnectorApi,
    connector_file: str,
    use_working_dir_file: bool = False,
    dry_run: bool = False,
):
    """Register new connector by sending a JSON or YAML file to the API."""

    if (
        converted_connector_content := get_api_file(
            api_file_path=connector_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
    ) is not None:
        try:

            if not dry_run:
                retrieved_connector = connector_api.register_connector(
                    connector=converted_connector_content
                )
            else:
                logger.info("DRY RUN - Would call connector_api.create_connector")
                retrieved_connector = converted_connector_content
                retrieved_connector["id"] = "<DRY RUN>"

            logger.debug(pformat(retrieved_connector))
            logger.info(f"Created new connector with id: {retrieved_connector['id']}")

        except UnauthorizedException:
            logger.error("Unauthorized access to the cosmotech api")

    else:
        logger.error(
            "Error : can not get correct Connector definition, please check your Connector.YAML file"
        )
