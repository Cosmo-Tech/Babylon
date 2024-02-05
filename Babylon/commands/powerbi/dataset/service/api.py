import logging
import jmespath

from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


class AzurePowerBIDatasetService:

    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def delete(self, workspace_id: str, force_validation: bool, dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        if not force_validation and not confirm_deletion("dataset", dataset_id):
            return CommandResponse.fail()

        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
        response = oauth_request(url, self.powerbi_token, type="DELETE")
        if response is None:
            return CommandResponse.fail()
        return response

    def get_all(self, workspace_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
        response = oauth_request(url, self.powerbi_token)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json().get("value")
        if filter:
            output_data = jmespath.search(filter, output_data)
        return output_data

    def get(self, workspace_id: str, dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
        response = oauth_request(url, self.powerbi_token)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        return output_data

    def take_over(self, workspace_id: str, dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/Default.TakeOver"
        response = oauth_request(url, self.powerbi_token, type="POST")
        if response is None:
            return CommandResponse.fail()
        logger.info(f"Successfully took ownership of dataset {dataset_id}")

    def update_credentials(self, workspace_id: str, dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        # First step, get datasources
        get_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/datasources"
        access_token = self.powerbi_token
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
