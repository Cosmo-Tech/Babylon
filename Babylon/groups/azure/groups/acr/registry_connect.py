import json
import logging
import subprocess

from azure.identity import DefaultAzureCredential
from azure.containerregistry import ContainerRegistryClient
import docker

from .....utils.credentials import pass_azure_credentials

logger = logging.getLogger("Babylon")


@pass_azure_credentials
def registry_connect(azure_credentials: DefaultAzureCredential,
                     registry: str) -> tuple[ContainerRegistryClient, docker.DockerClient]:
    # Login to registry
    registry_client = ContainerRegistryClient(f"https://{registry}",
                                              azure_credentials,
                                              audience="https://management.azure.com")
    registry_part = registry.split(".")[0]
    response = subprocess.run(["az", "acr", "login", "--name", registry_part, "--expose"],
                              shell=False,
                              check=False,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    decoded = json.loads(response.stdout)
    # Login to docker with the returned access token
    client = docker.from_env()
    try:
        client.login(username="00000000-0000-0000-0000-000000000000",
                     password=decoded.get("accessToken"),
                     registry=registry)
    except docker.errors.APIError:
        logger.error(f"Could not connect to container registry {registry}")
        return registry_client, client
    return registry_client, client
