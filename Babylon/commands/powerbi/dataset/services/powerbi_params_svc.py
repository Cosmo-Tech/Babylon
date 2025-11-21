import logging

from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")


class AzurePowerBIParamsService:
    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def get(self, workspace_id: str, dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        update_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/parameters"
        response = oauth_request(update_url, self.powerbi_token)
        if response is None:
            logger.info(f"[powerbi] failled to get dataset with id: {dataset_id}")
            return None
        output_data = response.json().get("value")
        return output_data

    def update(self, workspace_id: str, params: list[tuple[str, str]], dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        # Preparing parameter data
        details = {"updateDetails": [{"name": param.get("id"), "newValue": param.get("value")} for param in params]}
        update_url = (
            f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/Default.UpdateParameters"
        )
        response = oauth_request(update_url, self.powerbi_token, json=details, type="POST")
        if response is None:
            logger.info(f"[powerbi] failled to update dataset with id: {dataset_id}")
            return None
        logger.info("[powerbi] parameters successfully updated")
