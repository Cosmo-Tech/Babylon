import logging
import sys

from git import Optional
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")
env = Environment()


class ConnectorService:

    def __init__(self, azure_token: str, state: dict, spec: Optional[dict] = None):
        self.state = state
        self.spec = spec
        self.azure_token = azure_token
        self.url = state["api"]["url"]

        if not self.url:
            logger.error("API url not found")
            sys.exit(1)

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(
            f'{self.url}/connectors',
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def delete(self, force_validation: bool):
        connector_id = self.state["api"]["connector_id"]
        if not connector_id:
            logger.error('Connector_id is missing')
            sys.exit(1)
        if not force_validation and not confirm_deletion("connector", connector_id):
            return None
        response = oauth_request(
            f'{self.url}/connectors/{connector_id}',
            self.azure_token,
            type="DELETE",
        )
        return response

    def get_all(self):
        response = oauth_request(f'{self.url}/connectors', self.azure_token)
        return response

    def get(self):
        connector_id = self.state["api"]["connector_id"]
        if not connector_id:
            logger.error('Connector_id is missing')
            sys.exit(1)
        response = oauth_request(f'{self.url}/connectors/{connector_id}', self.azure_token)

        return response
