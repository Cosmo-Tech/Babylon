import logging
import typing

from azure.identity import DefaultAzureCredential
from click import command
from click import option
from click import make_pass_decorator

from ......utils.decorators import require_platform_key
from ..registry_connect import registry_connect

logger = logging.getLogger("Babylon")

pass_credentials = make_pass_decorator(DefaultAzureCredential)


@command()
@pass_credentials
@require_platform_key("acr_src_registry_name", "acr_src_registry_name")
@require_platform_key("acr_dest_registry_name", "acr_dest_registry_name")
@option("-r", "--registry", help="Container Registry name to scan, example: myregistry.azurecr.io")
def list(credentials: DefaultAzureCredential, acr_src_registry_name: str, acr_dest_registry_name: str,
         registry: typing.Optional[str]):
    """List all docker images in the specified registry"""
    registries = [registry] if registry else [acr_src_registry_name, acr_dest_registry_name]
    for reg in registries:
        cr_client, _ = registry_connect(reg, credentials)
        logger.info("Getting repositories stored in registry %s", reg)
        for repo in cr_client.list_repository_names():
            logger.info(f"repository: {repo}")
