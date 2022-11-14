import subprocess
import json
import logging

from azure.containerregistry import ContainerRegistryClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ServiceRequestError
import docker

logger = logging.getLogger("Babylon")


class AzureAcr:

    def __init__(self):
        self.cr_client = None
        self.docker_client = docker.from_env()
        self.registry = None

    def connect(self, credentials: DefaultAzureCredential, registry: str) -> docker.DockerClient:
        """Connects to a container registry

        :param credentials: Azure Credentials
        :type credentials: DefaultAzureCredential
        :param registry: Registry name
        :type registry: str
        :return: a logged docker client
        :rtype: docker.DockerClient
        """
        self.registry = registry
        self.cr_client = ContainerRegistryClient(f"https://{registry}",
                                                 credentials,
                                                 audience="https://management.azure.com")
        registry_part = registry.split(".")[0]
        response = subprocess.run(["az", "acr", "login", "--name", registry_part, "--expose"],
                                  shell=False,
                                  check=False,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        decoded = json.loads(response.stdout)
        # Login to docker with the returned access token
        try:
            self.docker_client.login(username="00000000-0000-0000-0000-000000000000",
                                     password=decoded.get("accessToken"),
                                     registry=registry)
        except docker.errors.APIError:
            logger.error(f"Could not connect to container registry {registry}")
            return self.docker_client
        return self.docker_client

    def list(self) -> list[str]:
        """Lists repositories in the connected registry

        :return: List of repository names
        :rtype: list[str]
        """
        logger.info("Getting repositories stored in registry %s", self.registry)
        try:
            repos = [str(repo) for repo in self.cr_client.list_repository_names()]
        except ServiceRequestError:
            logger.error(f"Could not list from registry {self.registry}")
            return []
        logger.info(repos)
        return repos

    def pull(self, repository: str):
        """Pulls a docker image from the ACR registry given in platform configuration"""
        repo = f"{self.registry}/{repository}"
        logger.info(f"Pulling remote repository {repository} from registry {self.registry}")
        try:
            img = self.docker_client.images.pull(repository=repo)
            logger.debug("Renaming local image without registry prefix")
            img.tag(repository)
            logger.debug("Removing local image with registry prefix")
            self.docker_client.images.remove(image=repo)
        except docker.errors.NotFound:
            logger.error(f"Repository {repository} not found in registry {self.registry} ")
            return
        except docker.errors.APIError as api_error:
            logger.error(api_error)
            return
        except Exception as e:
            logger.error(str(e))
        logger.info(f"Successfully pulled repository {repository} from registry {self.registry}")
