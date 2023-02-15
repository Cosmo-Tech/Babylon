import logging
from typing import Optional

from click import command
from click import option
from click import argument
from rich.pretty import pretty_repr

from ..........utils.request import oauth_request
from ..........utils.response import CommandResponse
from ..........utils.environment import Environment
from ..........utils.typing import QueryType
from ..........utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")


@command()
@argument("app_id", type=QueryType())
@option("-n", "--name", "password_name", help="Password display name")
@option("-s", "--select", "select", is_flag=True, help="Save secret in .secrets.yaml working dir file")
def create(app_id: str, password_name: Optional[str] = None, select: bool = False) -> CommandResponse:
    """
    Register a password or secret to an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-addpassword
    """
    route = f"https://graph.microsoft.com/v1.0/applications/{app_id}/addPassword"
    password_name = password_name or f"secret_{app_id}"
    details = {"passwordCredential": {"displayName": password_name}}
    response = oauth_request(route, get_azure_token("graph"), type="POST", json=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    env = Environment()
    if select:
        env.working_dir.set_yaml_key(".secrets.yaml", password_name, {
            "client_id": output_data["keyId"],
            "client_secret": output_data["secretText"]
        })
    return CommandResponse.success(output_data)
