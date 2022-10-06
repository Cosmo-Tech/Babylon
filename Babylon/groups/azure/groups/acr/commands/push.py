import logging
import docker
from click import command, make_pass_decorator, argument, option
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
"""

@command()
@requires_external_program("docker")
@pass_cr_client
@require_deployment_key("acr_registry_name", "acr_registry_name")
@argument("image")
@option("-t", "--tag", default="latest", show_default=True)
def push(cr_client: ContainerRegistryClient, acr_registry_name: str, image: str, tag: str):
    """Pulls a docker image from the ACR registry given in deployment configuration"""
    client = docker.from_env()
    try:
        image_obj = client.images.get(f"{image}:{tag}")
    except docker.errors.ImageNotFound:
        logger.error("Image %s not found locally", image)
        return
    logger.info("Pushing image %s:%s", image, tag)

    repo = image
    if ".azurecr.io/" not in image:
        repo = f"{acr_registry_name}.azurecr.io/{image}"
        image_obj.tag(repo, tag=tag)
    client.images.push(repository=repo, tag=tag)
