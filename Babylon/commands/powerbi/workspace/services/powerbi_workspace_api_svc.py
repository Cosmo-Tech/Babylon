import logging

import jmespath

from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzurePowerBIWorkspaceService:
    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.powerbi_token = powerbi_token
        self.state = state

    def create(self, name: str):
        url_groups = "https://api.powerbi.com/v1.0/myorg/groups?$workspaceV2=True"
        response = oauth_request(
            url=url_groups,
            access_token=self.powerbi_token,
            json={"name": name},
            type="POST",
        )
        if response is None:
            logger.warning("[powerbi] Cannot create PowerBI workspace")
            return None
        output_data = response.json()
        return output_data

    def delete(self, workspace_id: str, force_validation: bool):
        logger.info(f"Deleting workspace... {workspace_id}")
        if not workspace_id:
            logger.warning(f"Current value: {self.state['powerbi']['workspace']['id']}")
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        if not force_validation and not confirm_deletion("Power Bi Workspace", workspace_id):
            return CommandResponse.fail()
        url_delete = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
        response = oauth_request(url=url_delete, access_token=self.powerbi_token, type="DELETE")
        if response is None:
            logger.warning("[powerbi] Cannot delete PowerBI workspace")
            return CommandResponse.fail()
        return response

    def get_all(self, filter: bool = False):
        url_groups = "https://api.powerbi.com/v1.0/myorg/groups"
        response = oauth_request(url=url_groups, access_token=self.powerbi_token)
        if response is None:
            logger.warning(
                "[powerbi] Either workspace name list is empty or you are not allowed to access the PowerBI service"
            )
            return None
        output_data = response.json().get("value")
        if len(output_data) and filter:
            output_data = jmespath.search(filter, output_data)
        return output_data

    def get_current(self):
        workspace_id = self.state["powerbi"]["workspace"]["id"]
        url_groups = "https://api.powerbi.com/v1.0/myorg/groups"
        params = {"$filter": f"id eq '{workspace_id}'"}
        response = oauth_request(url_groups, self.powerbi_token, params=params)
        if response is None:
            logger.warning("[powerbi] Cannot get the current PowerBI workspace")
            return None
        workspace_data = response.json().get("value")
        if not workspace_data:
            logger.error(f"{workspace_id} not found")
            return None
        return workspace_data

    def get_by_name_or_id(self, name: str, workspace_id: str = ""):
        url_groups = "https://api.powerbi.com/v1.0/myorg/groups"
        params = {"$filter": f"id eq '{workspace_id}'"} if workspace_id else {"$filter": f"name eq '{name}'"}
        response = oauth_request(url_groups, self.powerbi_token, params=params)
        if response is None:
            logger.warning("[powerbi] Cannot get the PowerBI workspace by name or id")
            return None
        workspace_data = response.json().get("value")
        if not workspace_data:
            logger.error(f"{name} not found")
            return None
        if len(workspace_data):
            return workspace_data[0]
