import logging

from Babylon.utils.checkers import check_alphanum
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzureDirectoyPasswordService:

    def __init__(self, azure_token: str, state: dict = None) -> None:
        self.state = state
        self.azure_token = azure_token

    def create(self, object_id: str, password_name: str):
        check_alphanum(password_name)
        object_id = object_id or self.state['app_object_id']
        org_id: str = self.state['api_organization_id']
        work_key: str = self.state['api_workspace_key']
        route = f"https://graph.microsoft.com/v1.0/applications/{object_id}/addPassword"
        password_name = password_name or f"secret_{work_key}"
        details = {"passwordCredential": {"displayName": password_name}}
        response = oauth_request(route, self.azure_token, type="POST", json=details)
        if response is None:
            return CommandResponse.fail()
        output_data = response.json()
        d = dict(secret=output_data['secretText'])
        prefix = f'{env.organization_name}/{env.tenant_id}/projects/{env.context_id}'
        schema = f'{prefix}/{env.environ_id}/{org_id.lower()}/{work_key.lower()}/{password_name.lower()}'
        env.hvac_client.write(path=schema, **d)
        logger.info("Successfully created")
        return output_data

    def delete(self, key_id: str, object_id: str):
        logger.info(f"Deleting secret {key_id} of app registration {object_id}")
        route = f"https://graph.microsoft.com/v1.0/applications/{object_id}/removePassword"
        response = oauth_request(route, self.azure_token, type="POST", json={"keyId": key_id})
        if response is None:
            return CommandResponse.fail()
        logger.info(f"Successfully deleted secret of app registration {object_id}")
