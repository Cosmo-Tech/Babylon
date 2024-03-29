import jmespath

from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse


class AzureDirectoyGroupService:

    def __init__(self, azure_token: str) -> None:
        self.azure_token = azure_token

    def get_all(self, filter: bool):
        route = "https://graph.microsoft.com/v1.0/groups/"
        response = oauth_request(route, self.azure_token)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()["value"]
        if filter:
            output_data = jmespath.search(filter, output_data)
        return output_data
