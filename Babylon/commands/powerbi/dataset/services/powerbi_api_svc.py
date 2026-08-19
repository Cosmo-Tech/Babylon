from json import dumps
import logging

from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")


class AzurePowerBIDatasetService:
    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def delete(self, workspace_id: str, force_validation: bool, dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        if not force_validation and not confirm_deletion("dataset", dataset_id):
            return None

        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
        response = oauth_request(url, self.powerbi_token, type="DELETE")
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] failed to delete dataset with dataset_id: {dataset_id}")
            return None
        return response

    def get_all(self, workspace_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
        response = oauth_request(url, self.powerbi_token)
        if response is None:
            logger.error("  [bold red]✘[/bold red] failed to get all datasets")
            return None
        output_data = response.json().get("value")
        return output_data

    def get(self, workspace_id: str, dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
        response = oauth_request(url, self.powerbi_token)
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] failed to get dataset with dataset_id: {dataset_id}")
            return None
        output_data = response.json()
        return output_data

    def take_over(self, workspace_id: str, dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/Default.TakeOver"
        response = oauth_request(url, self.powerbi_token, type="POST")
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] failed to run TakeOver process on dataset_id : {dataset_id}")
            return None
        logger.info(f"  [bold green]✔[/bold green] Successfully took ownership of dataset {dataset_id}")

    def update_credentials(
        self,
        workspace_id: str,
        dataset_id: str,
        username: str | None = None,
        password: str | None = None,
    ):
        """
        Update credentials for Extension datasources in a Power BI dataset.
        """
        workspace_id = workspace_id or self.state.get("powerbi", {}).get("workspace", {}).get("id")
        # First step, get datasources
        datasources_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/datasources"

        response = oauth_request(datasources_url, self.powerbi_token)
        if response is None:
            logger.error(f"  [bold red]✘[/bold red] failed to update credentials on dataset_id : {dataset_id}")
            return None

        output_data = response.json().get("value", [])

        if username and password:
            credential_details = {
                "credentialDetails": {
                    "credentialType": "Basic",
                    "credentials": dumps(
                        {
                            "credentialData": [
                                {"name": "username", "value": username},
                                {"name": "password", "value": password},
                            ]
                        }
                    ),
                    "encryptedConnection": "Encrypted",
                    "encryptionAlgorithm": "None",
                    "privacyLevel": "Organizational",
                }
            }
        else:
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
            if datasource.get("datasourceType") != "PostgreSql":
                continue
            gateway_id = datasource.get("gatewayId")
            datasource_id = datasource.get("datasourceId")
            update_url = f"https://api.powerbi.com/v1.0/myorg/gateways/{gateway_id}/datasources/{datasource_id}"
            response = oauth_request(update_url, self.powerbi_token, json=credential_details, type="PATCH")
            if response is None:
                logger.error(f"  [bold red]✘[/bold red] could not update credentials for datasource {datasource_id}")
                continue
            logger.info(f"  [bold green]✔[/bold green] Successfully updated credentials for datasource {datasource_id}")