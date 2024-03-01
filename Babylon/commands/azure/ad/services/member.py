from venv import logger
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse


class AzureDirectoyMemberService:

    def __init__(self, azure_token: str) -> None:
        self.azure_token = azure_token

    def add(self, group_id: str, principal_id: str):
        route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
        details = {"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{principal_id}"}
        response = oauth_request(route, self.azure_token, type="POST", json=details)
        if response is None:
            return CommandResponse.fail()
        logger.info(f"Successfully added principal {principal_id} to group {group_id}")

    def get_all(self, group_id: str):
        route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/"
        response = oauth_request(route, self.azure_token, type="GET")
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        return output_data

    def remove(self, group_id: str, principal_id: str):
        route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/{principal_id}/$ref"
        logger.info(f"Deleting member {principal_id} from group {group_id}")
        response = oauth_request(route, self.azure_token, type="DELETE")
        if response is None:
            return CommandResponse.fail()
        logger.info(f"Successfully removed principal {principal_id} from group {group_id}")
