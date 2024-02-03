import docker
import logging

from azure.core.exceptions import HttpResponseError
from azure.core.exceptions import ResourceNotFoundError
from azure.core.exceptions import ServiceRequestError
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import get_registry_client
from Babylon.utils.clients import get_docker_client

logger = logging.getLogger("Babylon")
env = Environment()


class AzureContainerRegistryService:

    def __init__(self, state: dict = None) -> None:
        self.state = state

    def list(self, server: str = None):
        acr_login_server = server or self.state['acr']['login_server']
        cr_client = get_registry_client(acr_login_server)
        logger.info(f"Getting repositories stored in registry {acr_login_server}")
        try:
            repos = [repo for repo in cr_client.list_repository_names()]
        except ServiceRequestError:
            logger.error(f"Could not list from registry {acr_login_server}")
            return CommandResponse.fail()
        _ret: list[str] = [f"Respositories from {acr_login_server}:"]
        for repo in repos:
            props = cr_client.list_tag_properties(repository=repo)
            tags = [p.name for p in props]
            tags.sort(reverse=True)
            _ret.append(f" • {repo}: {tags}")
        logger.info("\n".join(_ret))

    def pull(self, image_tag: str):
        registry_server = self.state['acr']['login_server']
        simulator_repository = self.state['acr']['simulator_repository']
        simulator_version = self.state['acr']['simulator_version']
        image = image_tag or f"{simulator_repository}:{simulator_version}"
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
        # env.configuration.set_var(resource_id="acr", var_name="simulator_repository", var_value=image.split(":")[0])
        # env.configuration.set_var(resource_id="acr", var_name="simulator_version", var_value=image.split(":")[1])
        logger.info(f"Successfully pulled image {image} from registry {registry_server}")

    def push(self, image_tag: str):
        registry_server = self.state['acr']['login_server']
        simulator_repository = self.state['acr']['simulator_repository']
        simulator_version = self.state['acr']['simulator_version']
        image: str = image_tag or f"{simulator_repository}:{simulator_version}"
        client = get_docker_client(registry_server)
        if not client:
            return CommandResponse.fail()
        try:
            image_obj = client.images.get(image)
        except docker.errors.ImageNotFound:
            logger.error(f"Local image {image} not found")
            return CommandResponse.fail()
        logger.debug("Renaming image with registry prefix")
        ref_parts = image.split("/")
        if len(ref_parts) > 1:
            ref_parts[0] = registry_server
        else:
            ref_parts = [registry_server, *ref_parts]
        ref: str = "/".join(ref_parts)
        image_obj.tag(ref)
        logger.info(f"Pushing image {image} to {ref}")
        try:
            client.images.push(repository=ref)
        except docker.error.APIError as e:
            logger.error(f"Could not push image {image} to registry {registry_server}: {e}")
            return CommandResponse.fail()
        logger.debug("Removing local image with remote registry prefix")
        client.images.remove(ref)
        logger.info(f"Successfully pushed image {image} to registry {registry_server}")

    def delete(self, image_tag: str):
        registry_server = self.state['acr']['login_server']
        simulator_repository = self.state['acr']['simulator_repository']
        simulator_version = self.state['acr']['simulator_version']
        cr_client = get_registry_client(registry_server)
        image = image_tag or f"{simulator_repository}:{simulator_version}"
        if not image:
            logger.info(f"You trying to use the image in {env.context_id}.{env.environ_id}.acr.yaml")
            logger.info(f"Current value: {simulator_repository}:{simulator_version}")
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
