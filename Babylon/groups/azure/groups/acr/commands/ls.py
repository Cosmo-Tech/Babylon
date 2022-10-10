import os
import logging
from click import command, pass_context, Context, option
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")

"""Command Tests
> babylon acr ls
Should list all images in the registry given in config
> babylon acr ls -r my_registry
Should list all images in the given registry
Can be checked against `az acr repository list --name my_registry --output table`
"""


@command()
@pass_context
@require_deployment_key("acr_src_registry_name", "acr_src_registry_name")
@option("-r", "--registry")
def ls(ctx: Context, acr_src_registry_name: str, registry: str):
    """List all docker images in the specified registry"""
    registry = registry or acr_src_registry_name
    # Login to registry
    response = os.system(f"az acr login --name {registry}")
    if response:
        logger.error(f"Could not connect to registry {registry}")
        return
    cr_client = ContainerRegistryClient(
        f"https://{registry}",
        ctx.parent.obj,
        audience="https://management.azure.com")
    logger.info("Getting repositories stored in registry %s", registry)
    for repo in cr_client.list_repository_names():
        logger.info(f"repository: {repo}")
