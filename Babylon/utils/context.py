import glob
from pprint import pformat

import cosmotech_api
import yaml
from azure.identity import AzureCliCredential


class ContextObj:

    def __init__(self, logger):
        self.config = {}
        self.azure_credentials = None
        self.api_configuration = None

        self.logger = logger

        self.read_deployment_file()
        self.add_azure_credentials()
        self.add_api_configuration()

    def read_deployment_file(self):
        config_file_path = glob.glob('./deploy.yaml')
        if config_file_path:
            with open(config_file_path[0], 'r') as f:
                config = yaml.safe_load(f)
                self.config = config
                self.logger.debug("Existing parameters :")
                self.logger.debug(pformat(config))

    def add_azure_credentials(self):
        self.logger.debug(f"Adding Azure Credentials")
        credentials = AzureCliCredential()
        self.azure_credentials = credentials

    def add_api_configuration(self):
        if self.azure_credentials is None:
            return
        for key in ["api_url", "api_scope", "organization_id", "workspace_id"]:
            if key not in self.config:
                return
        else:
            self.logger.debug(f"Getting access token for given api scope")
            token = self.azure_credentials.get_token(self.config['api_scope'])

            self.logger.debug(f"Generating configuration to access cosmotech api")
            configuration = cosmotech_api.Configuration(
                host=self.config['api_url'],
                discard_unknown_keys=True,
                access_token=token.token
            )

        self.api_configuration = configuration
