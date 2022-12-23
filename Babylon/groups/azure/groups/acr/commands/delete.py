import logging
import typing

from azure.core.exceptions import HttpResponseError
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from click import Choice
from click import command
from click import make_pass_decorator
from click import option

from ..registry_connect import registry_connect
from ......utils.decorators import require_deployment_key
from ......utils.decorators import require_platform_key
from ......utils.decorators import timing_decorator
from ......utils.interactive import confirm_deletion
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")

pass_credentials = make_pass_decorator(DefaultAzureCredential)


@command()
@pass_credentials
@require_platform_key("csm_acr_registry_name", "csm_acr_registry_name")
@require_platform_key("acr_registry_name", "acr_registry_name")
@require_deployment_key("simulator_repository", "simulator_repository")
@require_deployment_key("simulator_version", "simulator_version")
@option("-r", "--registry", help="Container Registry name to delete from, example: myregistry.azurecr.io")
@option("-d", "--direction", type=Choice(["src", "dest"]), help="Container Registry to delete from")
@option("-i", "--image", help="Remote docker image to pull, example hello-world:latest")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@timing_decorator
def delete(credentials: DefaultAzureCredential,
           csm_acr_registry_name: str,
           acr_registry_name: str,
           simulator_repository: str,
           simulator_version: str,
           registry: typing.Optional[str] = None,
           direction: typing.Optional[str] = None,
           image: typing.Optional[str] = None,
           force_validation: typing.Optional[bool] = False) -> CommandResponse:
    """Delete docker image from selected repository"""
    registry = registry or {"src": csm_acr_registry_name, "dest": acr_registry_name}.get(direction)
    if not registry:
        logger.error("Please specify a registry to delete from with --direction or --registry")
        return CommandResponse.fail()
    cr_client, _ = registry_connect(registry, credentials)
    image = image or f"{simulator_repository}:{simulator_version}"
    image = f"{image}:latest" if ":" not in image else image
    try:
        props = cr_client.get_manifest_properties(*image.split(":"))
    except ResourceNotFoundError:
        logger.error(f"Image {image} not found in registry {registry}")
        return CommandResponse.fail()

    if not force_validation and not confirm_deletion("image", image):
        return CommandResponse.fail()

    logger.info(f"Deleting image {image} from registry {registry}")
    try:
        cr_client.delete_manifest(props.repository_name, props.digest)
    except HttpResponseError as e:
        logger.error(f"Could not delete image {image} from registry {registry}: {str(e)}")
        return CommandResponse.fail()
    logger.info(f"Successfully deleted image {image} from registry {registry}")
    return CommandResponse()
