import docker
import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import get_docker_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@timing_decorator
@option("-i", "--image", type=QueryType(), help="Remote docker image to pull, example hello-world:latest")
@option("-s", "--select", "select", is_flag=True, default=True, help="Select this repository in configuration")
@inject_context_with_resource({'acr': ['login_server', 'simulator_repository', 'simulator_version']}, required=False)
def pull(context: Any, select: bool, image: Optional[str] = None) -> CommandResponse:
    """
    Pulls a docker image from the ACR registry
    """
    registry_server = context['acr_login_server']
    image = image or f"{context['acr_simulator_repository']}:{context['acr_simulator_version']}"
    client = get_docker_client(registry=registry_server)
    if not client:
        return CommandResponse.fail()
    repo = f"{registry_server}/{image}"
    logger.info(f"Pulling remote image {image} from registry {registry_server}")
    try:
        img = client.images.pull(repository=repo)
        logger.debug("Renaming local image without registry prefix")
        img.tag(image)
        logger.debug("Removing local image with registry prefix")
        client.images.remove(image=repo)
    except docker.errors.NotFound:
        logger.error(f"Image {image} not found in registry {registry_server} ")
        return CommandResponse.fail()
    except docker.errors.APIError as api_error:
        logger.error(api_error)
        return CommandResponse.fail()
    except Exception as e:
        logger.error(str(e))
    if select:
        env.configuration.set_var(resource_id="acr", var_name="simulator_repository", var_value=image.split(":")[0])
        env.configuration.set_var(resource_id="acr", var_name="simulator_version", var_value=image.split(":")[1])
    logger.info(f"Successfully pulled image {image} from registry {registry_server}")
    return CommandResponse.success()
