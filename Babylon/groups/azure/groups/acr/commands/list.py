import json
import logging
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ServiceRequestError
from click import Choice
from click import command
from click import option
from click import Path
from click import make_pass_decorator
from rich.pretty import Pretty

from ......utils.decorators import require_platform_key
from ..registry_connect import registry_connect

logger = logging.getLogger("Babylon")

pass_credentials = make_pass_decorator(DefaultAzureCredential)


@command()
@pass_credentials
@require_platform_key("acr_src_registry_name", "acr_src_registry_name")
@require_platform_key("acr_dest_registry_name", "acr_dest_registry_name")
@option("-r", "--registry", help="Container Registry name to scan, example: myregistry.azurecr.io")
@option("-d", "--direction", type=Choice(["src", "dest"]), help="Container Registry choice to delete from")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where images should be outputted (json-formatted)",
    type=Path(writable=True),
)
def list(credentials: DefaultAzureCredential,
         acr_src_registry_name: str,
         acr_dest_registry_name: str,
         registry: Optional[str] = None,
         direction: Optional[str] = None,
         output_file: Optional[str] = None):
    """List all docker images in the specified registry"""
    registry = registry or {"src": acr_src_registry_name, "dest": acr_dest_registry_name}.get(direction)
    if not registry:
        logger.error("Please specify a registry to list from with --direction or --registry")
        return
    cr_client, _ = registry_connect(registry, credentials)
    logger.info(f"Getting repositories stored in {registry}")
    try:
        repos = [repo for repo in cr_client.list_repository_names()]
    except ServiceRequestError:
        logger.error(f"Could not list from registry {registry}")
        return
    if not output_file:
        logger.info(Pretty(repos))
        return
    with open(output_file, "w") as _file:
        json.dump(repos, _file, ensure_ascii=False)
    logger.info("Full content was dumped on %s.", output_file)
