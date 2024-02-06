import logging
import jmespath

from Babylon.utils.checkers import check_ascii
from Babylon.utils.request import oauth_request
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.interactive import confirm_deletion

logger = logging.getLogger("Babylon")
env = Environment()


class AzurePowerBIWorkspaceService:

    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def create(self, name: str):
        check_ascii(name)
        url_groups = "https://api.powerbi.com/v1.0/myorg/groups?$workspaceV2=True"
        response = oauth_request(
            url=url_groups,
            access_token=self.powerbi_token,
            json={"name": name},
            type="POST",
        )
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        # env.configuration.set_var(resource_id="powerbi", var_name=["workspace", "id"], var_value=output_data["id"])
        # logger.info(SUCCESS_CONFIG_UPDATED("powerbi", "id"))
        # env.configuration.set_var(resource_id="powerbi", var_name=["workspace", "name"], var_value=name)
        # logger.info(SUCCESS_CONFIG_UPDATED("powerbi", "name"))
        # logger.info(SUCCESS_CREATED("Workspace powerbi", output_data['id']))
        return output_data

    def delete(self, workspace_id: str, force_validation: bool):
        if not workspace_id:
            logger.warning(
                f"You trying to use workspace referenced in '{env.context_id}.{env.environ_id}.powerbi.yaml'"
            )
            logger.warning(f'Current value: {self.state["powerbi"]["workspace"]["id"]}')
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        if not force_validation and not confirm_deletion(
            "Power Bi Workspace", workspace_id
        ):
            return CommandResponse.fail()
        url_delete = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
        response = oauth_request(
            url=url_delete, access_token=self.powerbi_token, type="DELETE"
        )
        if response is None:
            return CommandResponse.fail()
        return response

    def get_all(self, filter: bool):
        url_groups = "https://api.powerbi.com/v1.0/myorg/groups"
        response = oauth_request(url=url_groups, access_token=self.powerbi_token)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json().get("value")
        if len(output_data) and filter:
            output_data = jmespath.search(filter, output_data)
        return output_data

    def get_current(self):
        workspace_id = self.state["powerbi"]["workspace"]["id"]
        url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
        params = {"$filter": f"id eq '{workspace_id}'"}
        response = oauth_request(url_groups, self.powerbi_token, params=params)
        if response is None:
            return CommandResponse.fail()
        workspace_data = response.json().get('value')
        if not workspace_data:
            logger.error(f"{workspace_id} not found")
            return CommandResponse.fail()
        return workspace_data

    def get(self, workspace_id: str, name: str):
        if not workspace_id:
            logger.info("You trying to use key : workspace id referenced in configuration")
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
        params = {"$filter": f"id eq '{workspace_id}'"} if workspace_id else {"$filter": f"name eq '{name}'"}
        response = oauth_request(url_groups, self.powerbi_token, params=params)
        if response is None:
            return CommandResponse.fail()
        workspace_data = response.json().get('value')
        if not workspace_data:
            logger.error(f"{name} not found")
            return CommandResponse.fail()
        if len(workspace_data):
            workspace_id = workspace_data[0]['id']
            # env.configuration.set_var(resource_id="powerbi", var_name=["workspace", "id"], var_value=workspace_id)
            # logger.info(SUCCESS_CONFIG_UPDATED("workspace", "id"))
            # env.configuration.set_var(resource_id="powerbi", var_name=["workspace", "name"], var_value=name)
            # logger.info(SUCCESS_CONFIG_UPDATED("workspace", "name"))
            return workspace_data[0]
