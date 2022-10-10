import os
import logging
from click import command, make_pass_decorator, pass_context, Context
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")

"""Command Tests
> babylon acr ls
Should list all images in the given registry
Can be checked against `az acr repository list --name my_registry --output table`
"""

@command()
@pass_context
@require_deployment_key("acr_src_registry_name", "acr_src_registry_name")
def ls(ctx: Context, acr_src_registry_name: str):
    """List all docker images in the specified registry"""
    # Login to registry
    os.system(f"az acr login --name {acr_src_registry_name}")
    cr_client = ContainerRegistryClient(
        f"https://{acr_src_registry_name}",
        ctx.parent.obj,
        audience="https://management.azure.com")
    logger.info("Getting repositories stored in registry %s", acr_src_registry_name)
    for repo in cr_client.list_repository_names():
        logger.info(f"repository: {repo}")
