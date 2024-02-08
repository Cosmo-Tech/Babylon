import logging

from typing import Any
from click import option
from click import command
from click import argument
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.commands.azure.ad.app.password.service.api import (
    AzureDirectoyPasswordService,
)

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_azure_token("graph")
@option("--key", "key_id", help="Password Key ID", required=True, type=QueryType())
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("object_id", type=QueryType())
@retrieve_state
def delete(
    state: Any,
    azure_token: str,
    object_id: str,
    key_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a password for an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-removepassword
    """
    if not force_validation and not confirm_deletion("secret", key_id):
        return CommandResponse.fail()
    service = AzureDirectoyPasswordService(azure_token=azure_token, state=state)
    service.delete(key_id=key_id, object_id=object_id)
    return CommandResponse.success()
