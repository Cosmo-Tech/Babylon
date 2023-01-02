import logging

from azure.core.credentials import AccessToken
from click import command
from click import argument
from click import pass_context
from click import Context
from click import option

from ......utils.response import CommandResponse
from ......utils.typing import QueryType
from ......utils.request import oauth_request
from ......utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("dataset_id", type=QueryType())
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
def update_credentials(ctx: Context, powerbi_workspace_id: str, dataset_id: str, workspace_id: str) -> CommandResponse:
    """Update azure credentials of a given datasource"""
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    access_token = ctx.find_object(AccessToken).token

    # First step, get datasources
    get_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/datasources"
    response = oauth_request(url=get_url, access_token=access_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")

    # Then update credentials for Extension datasources
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
        response = oauth_request(url=update_url, access_token=access_token, json_data=credential_details, type="PATCH")
        if response is None:
            logger.error(f"Could not update credentials of datasource {datasource_id}")
            continue
        logger.info(f"Successfully updated credentials of datasource {datasource_id}")
    return CommandResponse()
