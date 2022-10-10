import os
import logging
import docker
from click import command, pass_context, argument, option
from click.core import Context
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import require_deployment_key

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
@require_deployment_key("acr_src_registry_name", "acr_src_registry_name")
@require_deployment_key("acr_image_reference", "acr_image_reference")
@argument("image")
@option("-r", "--registry")
def pull(ctx: Context, acr_src_registry_name: str, acr_image_reference: str, registry: str, image: str):
    """Pulls a docker image from the ACR registry given in deployment configuration"""
    registry = registry or acr_src_registry_name
    image = image or acr_image_reference
    # Login to registry
    os.system(f"az acr login --name {registry}")
    ContainerRegistryClient(
        f"https://{registry}",
        ctx.parent.obj,
        audience="https://management.azure.com")
    # Pulling image
    client = docker.from_env()
    logger.info(f"Pulling image {image}")
    repo = f"{registry}/{image}"
    try:
        client.images.pull(repository=repo)
    except docker.errors.NotFound:
        logger.error(
            f"Registry {registry} does not contain {image}")
    except docker.errors.APIError as api_error:
        logger.error(f"API Error: {api_error}")
