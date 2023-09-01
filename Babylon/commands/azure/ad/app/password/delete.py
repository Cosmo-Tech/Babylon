import logging

from click import command
from click import option
from click import argument
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@option("--key", "key_id", help="Password Key ID", required=True, type=QueryType())
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("object_id", type=QueryType())
def delete(azure_token: str, object_id: str, key_id: str, force_validation: bool = False) -> CommandResponse:
    """
    Delete a password for an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-removepassword
    """
    if not force_validation and not confirm_deletion("secret", key_id):
        return CommandResponse.fail()
    logger.info(f"Deleting secret {key_id} of app registration {object_id}")
    route = f"https://graph.microsoft.com/v1.0/applications/{object_id}/removePassword"
    response = oauth_request(route, azure_token, type="POST", json={"keyId": key_id})
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully deleted secret of app registration {object_id}")
    return CommandResponse.success()
