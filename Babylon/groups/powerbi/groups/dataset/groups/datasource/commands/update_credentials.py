import logging
import requests
from typing import Optional
import json

from click import command
from click import argument
from click import pass_context
from click import Context
from click import option

from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("datasource_id")
@option("-g", "--gateway-id", "gateway_id", help="PowerBI datasource gateway ID")
def update_credentials(ctx: Context, datasource_id: str, gateway_id: Optional[str] = None) -> CommandResponse:
    """Get datasource details of a given dataset"""
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    update_url = f"https://api.powerbi.com/v1.0/myorg/gateways/{gateway_id}/datasources/{datasource_id}"
    credential_details = {
        "credentialDetails": {
            "credentialType": "OAuth2",
            "credentials": json.dumps({"credentialData": [{
                "name": "accessToken",
                "value": f"{access_token}"
            }]}),
            "encryptedConnection": "Encrypted",
            "encryptionAlgorithm": "None",
            "privacyLevel": "Organizational",
        }
    }
    try:
        response = requests.patch(url=update_url, headers=header, json=credential_details)
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    if response.status_code != 200:
        logger.error("Request failed: %s", response.reason)
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    report_data = response.json().get("value")
    logger.info(report_data)
    return CommandResponse(data=report_data)
