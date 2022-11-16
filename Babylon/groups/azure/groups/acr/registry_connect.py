import json
import logging
import subprocess

from azure.containerregistry import ContainerRegistryClient
from azure.identity import DefaultAzureCredential
import docker

logger = logging.getLogger("Babylon")


def registry_connect(registry: str,
                     credentials: DefaultAzureCredential) -> tuple[ContainerRegistryClient, docker.DockerClient]:
    # Login to registry
    registry_client = ContainerRegistryClient(f"https://{registry}",
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
    client = docker.from_env()
    try:
        client.ping()
    except Exception:
        logger.error("Could not ping local docker client, check if the docker service is running")
        return registry_client, client
    try:
        client.login(username="00000000-0000-0000-0000-000000000000",
                     password=decoded.get("accessToken"),
                     registry=registry)
    except docker.errors.APIError:
        logger.error(f"Could not connect to container registry {registry}")
        return registry_client, client
    return registry_client, client
