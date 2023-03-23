import logging

from click import argument
from click import command
from click import option

from ....utils.interactive import confirm_deletion
from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import require_platform_key
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@pass_azure_token("csm_api")
@require_platform_key("api_url")
@argument("connector-id", type=QueryType())
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def delete(
    azure_token: str,
    api_url: str,
    connector_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """Delete a registered connector"""
    if not force_validation and not confirm_deletion("connector", connector_id):
        return CommandResponse.fail()
    response = oauth_request(f"{api_url}/connectors/{connector_id}", azure_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully deleted connector {connector_id}")
    return CommandResponse.success()
