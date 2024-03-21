import logging

from Babylon.utils.checkers import check_email
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


class AzurePowerBUsersIService:

    def __init__(self, powerbi_token: str, state: dict = None) -> None:
        self.state = state
        self.powerbi_token = powerbi_token

    def add(self, email: str, workspace_id: str, dataset_id: str):
        workspace_id = workspace_id or self.state["powerbi"]["workspace"]["id"]
        identifier = email or self.state["azure"]["email"]
        check_email(identifier)
        gate_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/users"
        credential_details = {"identifier": identifier, "principalType": "User", "datasetUserAccessRight": "Read"}
        response = oauth_request(gate_url, self.powerbi_token, json=credential_details, type="POST")
        if response is None:
            return CommandResponse.fail()
        logger.info("Successfully added")
        return response
