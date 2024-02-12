import logging

from pathlib import Path
from posixpath import basename
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")
env = Environment()


class ApiConnectorService:

    def __init__(self, azure_token: str, state: dict = None) -> None:
        self.state = state
        self.azure_token = azure_token
        self.url = self.state["api"]["url"]

    def create(self, connector_file: Path):
        if not connector_file:
            logger.error("option --payload is missing")
            return None
        if not connector_file.exists():
            logger.error(f"No such file: '{basename(connector_file)}' in directory")
            return None
        details = env.fill_template(connector_file)
        response = oauth_request(
            f'{self.url}/connectors',
            self.azure_token,
            type="POST",
            data=details,
        )
        if response is None:
            return None
        response = response.json()
        return response

    def delete(self, force_validation: bool, id: str):
        if not force_validation and not confirm_deletion("connector", id):
            return None
        response = oauth_request(
            f'{self.url}/connectors/{id}',
            self.azure_token,
            type="DELETE",
        )
        if response is None:
            return None
        return True

    def get_all(self):
        response = oauth_request(f'{self.url}/connectors', self.azure_token)
        if response is None:
            return None
        connectors = response.json()
        return connectors

    def get(self, id: str):
        response = oauth_request(f'{self.url}/connectors/{id}', self.azure_token)
        if response is None:
            return None
        connector = response.json()
        return connector
