import logging

from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")


class AzurePowerBIWorkspaceUserService:
    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def add(self, workspace_id: str, right: str, type: str, email: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        identifier = email or self.state["azure"]["email"]
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        body = {
            "identifier": identifier,
            "groupUserAccessRight": right,
            "principalType": type,
        }
        response = oauth_request(url_users, self.powerbi_token, json=body, type="POST")
        if response is None:
            logger.error(f"[powerbi] failed to add identifier with email: {identifier}")
            return None
        logger.info("[powerbi] identifier successfully added")

    def delete(self, workspace_id, force_validation: bool, email: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users/{email}"
        if not force_validation and not confirm_deletion("user", email):
            return None
        response = oauth_request(url_users, self.powerbi_token, type="DELETE")
        if response is None:
            logger.error(f"[powerbi] failed to delete identifier with email: {email}")
            return None
        logger.info("[powerbi] identifier successfully removed")

    def get_all(self, workspace_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        response = oauth_request(url_users, self.powerbi_token)
        if response is None:
            logger.error("[powerbi] failed to get all identifier")
            return None
        output_data = response.json().get("value")
        return output_data

    def update(self, workspace_id: str, right: str, type: str, email: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        body = {
            "identifier": email,
            "groupUserAccessRight": right,
            "principalType": type,
        }
        response = oauth_request(url_users, self.powerbi_token, json=body, type="PUT")
        if response is None:
            logger.error("[powerbi] failed to update identifier")
            return None
        logger.info("[powerbi] identifier successfully updated")
        return response
