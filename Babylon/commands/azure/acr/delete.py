import logging

from typing import Any, Optional
from azure.core.exceptions import HttpResponseError
from azure.core.exceptions import ResourceNotFoundError
from click import command
from click import option
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.clients import get_registry_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@option("--image", type=QueryType(), help="Remote docker image to pull, example hello-world:latest")
@option("-D", "force_validation", is_flag=True, default=True, help="Force Delete")
@inject_context_with_resource({'acr': ['login_server', 'simulator_repository', 'simulator_version']}, required=False)
def delete(context: Any, image: Optional[str] = None, force_validation: Optional[bool] = False) -> CommandResponse:
    """
    Delete docker image from selected repository
    """
    registry_server = context['acr_login_server']
    cr_client = get_registry_client(registry_server)
    image = image or f"{context['acr_simulator_repository']}:{context['acr_simulator_version']}"
    if not image:
        logger.info(f"You trying to use the image in {env.context_id}.{env.environ_id}.acr.yaml")
        logger.info(f"Current value: {context['acr_simulator_repository']}:{context['acr_simulator_version']}")
    if not force_validation and not confirm_deletion("image", image):
        return CommandResponse.fail()

    image = f"{image}:latest" if ":" not in image else image
    try:
        props = cr_client.get_manifest_properties(*image.split(":"))
    except ResourceNotFoundError:
        logger.error(f"Image {image} not found in registry {registry_server}")
        return CommandResponse.fail()

    logger.info(f"Deleting image {image} from registry {registry_server}")
    try:
        cr_client.delete_manifest(props.repository_name, props.digest)
    except HttpResponseError as e:
        logger.error(f"Could not delete image {image} from registry {registry_server}: {str(e)}")
        return CommandResponse.fail()
    logger.info(f"Successfully deleted image {image} from registry {registry_server}")
    return CommandResponse.success()
