import os
import logging
import json
import docker
from click import command, make_pass_decorator, pass_context, argument, option
from click.core import Context
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import require_deployment_key

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
@require_deployment_key("acr_dest_registry_name", "acr_dest_registry_name")
@require_deployment_key("acr_image_reference", "acr_image_reference")
@argument("image")
@option("-r", "--registry")
def push(ctx: Context, acr_dest_registry_name: str, acr_image_reference: str, image: str, registry: str):
    """Push a docker image to the ACR registry given in deployment configuration"""
    registry = registry or acr_dest_registry_name
    image = image or acr_image_reference
    # Login to registry
    os.system(f"az acr login --name {registry}")
    ContainerRegistryClient(
        f"https://{registry}",
        ctx.parent.obj,
        audience="https://management.azure.com")

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
    ref = "/".join(ref_parts)
    image_obj.tag(ref)
    response = client.images.push(repository=ref)

    # Log status
    for resp in response.split("\n"):
        if resp:
            logger.debug(json.loads(resp).get("status", ""))
