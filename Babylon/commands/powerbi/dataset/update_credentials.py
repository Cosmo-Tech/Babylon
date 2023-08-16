import logging
from typing import Any

from click import command
from click import argument
from click import option

from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@pass_powerbi_token()
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@argument("dataset_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def update_credentials(
    context: Any,
    powerbi_token: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Update azure credentials of a given datasource
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    # First step, get datasources
    get_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/datasources"
    access_token = powerbi_token
    response = oauth_request(get_url, access_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")
    credential_details = {
        "credentialDetails": {
            "credentialType": "OAuth2",
            "useCallerAADIdentity": True,
            "encryptedConnection": "Encrypted",
            "encryptionAlgorithm": "None",
            "privacyLevel": "Organizational",
        }
    }
    for datasource in output_data:
        if datasource.get("datasourceType") != "Extension":
            continue
        gateway_id = datasource.get('gatewayId')
        datasource_id = datasource.get('datasourceId')
        update_url = f"https://api.powerbi.com/v1.0/myorg/gateways/{gateway_id}/datasources/{datasource_id}"
        response = oauth_request(update_url, access_token, json=credential_details, type="PATCH")
        if response is None:
            logger.error(f"Could not update credentials of datasource {datasource_id}")
            continue
        logger.info(f"Successfully updated credentials of datasource {datasource_id}")
    return CommandResponse()
