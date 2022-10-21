import logging
import subprocess
import typing

from azure.containerregistry import ContainerRegistryClient
from click import command
from click import Context
from click import option
from click import pass_context
import docker

from ......utils.decorators import require_deployment_key, require_platform_key

logger = logging.getLogger("Babylon")
"""Command Tests
> babylon azure acr pull
Should add a new entry to `docker image ls`
> babylon azure acr pull my_image:latest
Should add a new entry to `docker image ls`
> babylon azure acr pull -r my_registry my_image:my_tag
Should add new entry to `docker image ls`
"""


@command()
@pass_context
@require_platform_key("acr_registry_name", "acr_registry_name")
@require_deployment_key("acr_image_reference", "acr_image_reference")
@option("-i", "--image", help="Local docker image to pull")
@option("-r", "--registry", help="Container Registry name to pull from, example: myregistry.azurecr.io")
def pull(ctx: Context, acr_registry_name: str, acr_image_reference: str, registry: typing.Optional[str],
         image: typing.Optional[str]):
    """Pulls a docker image from the ACR registry given in platform configuration"""
    registry = registry or acr_registry_name
    image = image or acr_image_reference
    # Login to registry
    response = subprocess.run(["az", "acr", "login", "--name", registry],
                              shell=False,
                              check=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    if response.returncode:
        logger.error(f"Could not connect to registry {registry}: {str(response.stderr)}")
        return
    ContainerRegistryClient(f"https://{registry}", ctx.parent.obj, audience="https://management.azure.com")
    # Pulling image
    client = docker.from_env()
    logger.info(f"Pulling image {image}")
    repo = f"{registry}/{image}"
    try:
        client.images.pull(repository=repo)
    except docker.errors.NotFound:
        logger.error(f"Registry {registry} does not contain {image}")
    except docker.errors.APIError as api_error:
        logger.error(f"API {api_error}")
