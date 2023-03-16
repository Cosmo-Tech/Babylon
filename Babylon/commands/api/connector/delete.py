from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import option
from cosmotech_api.api.connector_api import ConnectorApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ....utils.typing import QueryType
from ....utils.api import get_api_file
from ....utils.interactive import confirm_deletion
from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **connector_api.unregister_connector** and unregister a Connector")
@timing_decorator
@pass_api_client
@argument(
    "connector_id",
    required=False,
    type=QueryType(),
)
@option(
    "-i",
    "--connector-file",
    "connector_file",
    help="In case the connector id is retrieved from a file",
)
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def delete(
    api_client: ApiClient,
    connector_id: str,
    connector_file: Optional[str] = None,
    force_validation: Optional[bool] = False,
    use_working_dir_file: Optional[bool] = False,
) -> CommandResponse:
    """Unregister a Connector via Cosmotech API."""
    connector_api = ConnectorApi(api_client)
    if not connector_id:
        if not connector_file:
            logger.error("No id passed as argument or option use -i option"
                         " to pass an json or yaml file containing an connector id.")
            return CommandResponse.fail()

        converted_connector_content = get_api_file(api_file_path=connector_file,
                                                   use_working_dir_file=use_working_dir_file)
        if not converted_connector_content:
            logger.error("Can not get Connector definition, please check your file")
            return CommandResponse.fail()

        if "id" not in converted_connector_content and "dataset_id" not in converted_connector_content:
            logger.error(f"Could not found connector id in {connector_file}.")
            return CommandResponse.fail()

        try:
            connector_id = converted_connector_content["id"]
        except KeyError:
            connector_id = converted_connector_content["dataset_id"]

    try:
        connector_api.find_connector_by_id(connector_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Connector with id {connector_id} not found.")
        return CommandResponse.fail()

    if not force_validation and not confirm_deletion("connector", connector_id):
        return CommandResponse.fail()

    logger.info(f"Deleting connector {connector_id}")

    try:
        connector_api.unregister_connector(connector_id)
        logger.info(f"Connector with id {connector_id} deleted.")
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return CommandResponse.fail()
    except ForbiddenException:
        logger.error(f"You are not allowed to delete the connector {connector_id}")
        return CommandResponse.fail()
    return CommandResponse.success()