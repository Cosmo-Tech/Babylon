import logging
import jmespath

from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.interactive import confirm_deletion

logger = logging.getLogger("Babylon")


class AzurePowerBIWorkspaceUserService:

    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def add(self, workspace_id: str, right: str, type: str, email: str):
        logger.info(f"Adding {email}")
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
            return CommandResponse.fail()
        logger.info("Successfully added")

    def delete(self, workspace_id, force_validation: bool, email: str):
        logger.info(f"Deleting {email}")
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url_users = (
            f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users/{email}"
        )
        if not force_validation and not confirm_deletion("user", email):
            return CommandResponse.fail()
        response = oauth_request(url_users, self.powerbi_token, type="DELETE")
        if response is None:
            return CommandResponse.fail()
        logger.info("Successfully removed")

    def get_all(self, workspace_id: str, filter: bool = False):
        logger.info("Getting all")
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        response = oauth_request(url_users, self.powerbi_token)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json().get("value")
        if filter:
            output_data = jmespath.search(filter, output_data)
        return output_data

    def update(self, workspace_id: str, right: str, type: str, email: str):
        logger.info(f"Updating {email}")
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url_users = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        body = {
            "identifier": email,
            "groupUserAccessRight": right,
            "principalType": type,
        }
        response = oauth_request(url_users, self.powerbi_token, json=body, type="PUT")
        if response is None:
            return CommandResponse.fail()
        logger.info("Successfully updated")
        return response
