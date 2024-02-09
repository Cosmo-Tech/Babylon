import logging
import jmespath

from git import Optional
from pathlib import Path
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class ApiConnectorService:

    def __init__(self, azure_token: str, state: dict = None) -> None:
        self.state = state
        self.azure_token = azure_token

    def create(self, connector_file: Path):
        details = env.fill_template(connector_file)
        response = oauth_request(
            f'{self.state["api"]["url"]}/connectors',
            self.azure_token,
            type="POST",
            data=details,
        )
        if response is None:
            return CommandResponse.fail()
        response = response.json()
        return response

    def delete(self, force_validation: bool, id: str):
        if not force_validation and not confirm_deletion("connector", id):
            return CommandResponse.fail()
        response = oauth_request(
            f'{self.state["api"]["url"]}/connectors/{id}',
            self.azure_token,
            type="DELETE",
        )
        if response is None:
            return CommandResponse.fail()

    def get_all(self, filter: Optional[str] = None):
        response = oauth_request(f'{self.state["api"]["url"]}/connectors', self.azure_token)
        if response is None:
            return CommandResponse.fail()
        connectors = response.json()
        if len(connectors) and filter:
            connectors = jmespath.search(filter, connectors)
        return connectors

    def get(self, id: str):
        response = oauth_request(f'{self.state["api"]["url"]}/connectors/{id}', self.azure_token)
        if response is None:
            return CommandResponse.fail()
        connector = response.json()
        return connector
