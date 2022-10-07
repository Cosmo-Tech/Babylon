import os
import logging
import json
import docker
from click import command, make_pass_decorator, pass_context
from click.core import Context
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import requires_external_program, require_deployment_key

logger = logging.getLogger("Babylon")

pass_cr_client = make_pass_decorator(ContainerRegistryClient)

"""Command Tests
> babylon acr push this_image_does_not_exist
Should provide a clean error log
> babylon acr push existing_image -t tag_that_does_not_exists
Should provide a clean error log
> babylon acr push existing_image -t existing_tag
Should add a new entry to `az acr repository list --name my_registry`
> babylon acr pull existing_image
Should a new entry to `az acr repository list --name my_registry` with the `latest` tag
> babylon acr push existing_image.azurecr.io
Should add a new entry to `az acr repository list --name my_registry`
"""


@command()
@requires_external_program("docker")
@pass_context
@require_deployment_key("acr_dest_registry_name", "acr_dest_registry_name")
@require_deployment_key("acr_image_reference", "acr_image_reference")
def push(ctx: Context, acr_dest_registry_name: str, acr_image_reference: str):
    """Push a docker image to the ACR registry given in deployment configuration"""

    # Login to registry
    os.system(f"az acr login --name {acr_dest_registry_name}")
    ContainerRegistryClient(
        f"https://{acr_dest_registry_name}",
        ctx.parent.obj,
        audience="https://management.azure.com")

    # Retrieve image
    client = docker.from_env()
    try:
        image_obj = client.images.get(acr_image_reference)
    except docker.errors.ImageNotFound:
        logger.error("Image %s not found locally", acr_image_reference)
        return
    logger.info("Pushing image %s", acr_image_reference)

    # Rename image with registry url if it is not present
    ref_parts = acr_image_reference.split("/")
    if len(ref_parts) > 1:
        ref_parts[0] = acr_dest_registry_name
    else:
        ref_parts = [acr_dest_registry_name, *ref_parts]
    ref = "/".join(ref_parts)
    image_obj.tag(ref)
    response = client.images.push(repository=ref)

    # Log status
    for resp in response.split("\n"):
        if resp:
            logger.debug(json.loads(resp).get("status", ""))
