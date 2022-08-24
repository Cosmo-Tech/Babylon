import glob
from pprint import pformat
import errno
import os

import cosmotech_api
import yaml
from azure.identity import AzureCliCredential, DefaultAzureCredential


class ContextObj:

    def check_required_configuration(self, configuration_list: list):
        missing_configurations = [configuration for configuration in configuration_list if
                                  configuration not in self.config]
        for conf in missing_configurations:
            self.logger.error(f"The configuration parameter {conf} is missing " +
                              "please make sure it is present in your 'deploy.yaml' file")
        return len(missing_configurations) == 0

    def __init__(self, logger, azure=False, api=False, config=False):
        self.config = {}
        self.azure_credentials = None
        self.api_configuration = None

        self.logger = logger

        if config:
            self.read_deployment_file()
        if azure:
            self.add_azure_credentials()
        if api:
            self.add_api_configuration()

    def read_deployment_file(self):
        config_file_path = glob.glob('./deploy.yaml')
        if config_file_path:
            with open(config_file_path[0], 'r') as f:
                config = yaml.safe_load(f)
                self.config = config
                self.logger.debug("Existing parameters :")
                self.logger.debug(pformat(config))
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), './deploy.yaml')

    def add_azure_credentials(self):
        self.logger.debug(f"Adding Azure Credentials")
        try:
            credentials = AzureCliCredential()
        except:
            credentials = DefaultAzureCredential()
        self.azure_credentials = credentials
        self.config['azure_credentials'] = self.azure_credentials


    def add_api_configuration(self):
        if self.azure_credentials is None:
            self.logger.error("You cannot use the cosmo api without an azure credentials.")
            return
        if not self.check_required_configuration(["api_url", "api_scope", "organization_id", "workspace_id"]):
            return
        self.logger.debug(f"Getting access token for given api scope")
        token = self.azure_credentials.get_token(self.config['api_scope'])

        self.logger.debug(f"Generating configuration to access cosmotech api")
        configuration = cosmotech_api.Configuration(
            host=self.config['api_url'],
            discard_unknown_keys=True,
            access_token=token.token
        )

        self.api_configuration = configuration
        self.config['api_configuration'] = self.api_configuration
