import json
import logging
import subprocess
import typing

import docker
from azure.containerregistry import ContainerRegistryClient
from click import Context
from click import command
from click import make_pass_decorator
from click import option
from click import pass_context

from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")

pass_cr_client = make_pass_decorator(ContainerRegistryClient)
"""Command Tests
> babylon azure acr push this_image_does_not_exist
Should provide a clean error log
> babylon azure acr push existing_image:tag_that_does_not_exist
Should provide a clean error log
> babylon azure acr push existing_image:existing_tag
Should add a new entry to `az acr repository list --name my_registry`
> babylon azure acr push existing_image -r my_registry
Should a new entry to `az acr repository list --name my_registry` with the `latest` tag
> babylon azure acr push
Should a new entry to `az acr repository list --name my_registry` with the values specified in conf
"""


@command()
@pass_context
@require_platform_key("acr_registry_name", "acr_registry_name")
@require_deployment_key("acr_image_reference", "acr_image_reference")
@option("-i", "--image", help="Local docker image to push")
@option("-r", "--registry", help="Container Registry name to push to, example: myregistry.azurecr.io")
def push(ctx: Context, acr_registry_name: str, acr_image_reference: str, image: typing.Optional[str],
         registry: typing.Optional[str]):
    """Push a docker image to the ACR registry given in platform configuration"""
    registry: str = registry or acr_registry_name
    image: str = image or acr_image_reference
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

    # Retrieve image
    client = docker.from_env()
    try:
        image_obj = client.images.get(image)
    except docker.errors.ImageNotFound:
        logger.error(f"Image {image} not found locally")
        return
    logger.info(f"Pushing image {image}")

    # Rename image with registry url if it is not present
    ref_parts = image.split("/")
    if len(ref_parts) > 1:
        ref_parts[0] = registry
    else:
        ref_parts = [registry, *ref_parts]
    ref: str = "/".join(ref_parts)
    image_obj.tag(ref)
    logs: str = client.images.push(repository=ref)

    # Log status
    for resp in logs.split("\n"):
        if resp:
            logger.debug(json.loads(resp).get("status", ""))
