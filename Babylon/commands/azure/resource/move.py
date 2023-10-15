import uuid
import yaml
import logging
import pathlib

from click import Path, command, option
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import timing_decorator
from azure.mgmt.resource import ResourceManagementClient
from Babylon.utils.credentials import get_azure_credentials
from azure.mgmt.authorization import AuthorizationManagementClient

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@option("--context", "context_id")
@option("--source", "source")
@option("--destination", "destination")
@option("--item", "items", multiple=True)
@option("--resources-file",
        "resources_file",
        type=Path(path_type=pathlib.Path, exists=True),
        help="File containing list of resources")
@timing_decorator
def move(context_id: str, source: str, destination: str, resources_file: pathlib.Path, items: list) -> CommandResponse:
    """
    Move resource to another resource group
    """
    azure_subscription = env.configuration.get_var(resource_id="azure",
                                                   var_name="subscription_id",
                                                   context_id=context_id,
                                                   environ_id=destination)
    source_rg = env.configuration.get_var(resource_id="azure",
                                          var_name="resource_group_name",
                                          context_id=context_id,
                                          environ_id=source)
    destination_rg = env.configuration.get_var(resource_id="azure",
                                               var_name="resource_group_name",
                                               context_id=context_id,
                                               environ_id=destination)

    # build source list
    resources_to_move = list()
    if resources_file and resources_file.exists():
        if resources_file.suffix in [".json"]:
            logger.error("json file not supported")
            return CommandResponse.fail()
        resources_to_move = yaml.load(resources_file.open("r"), Loader=yaml.SafeLoader)
    _items = list(map(lambda x: {"name": x}, items))
    resources_to_move = resources_to_move + _items
    resources_to_move = [i.get('name') for i in resources_to_move]

    # babylon client
    baby_client_id_dest = env.configuration.get_var(resource_id="babylon",
                                                    var_name="client_id",
                                                    context_id=context_id,
                                                    environ_id=destination)
    azure_credential = get_azure_credentials(baby_client_id=baby_client_id_dest, environ_id=destination)
    arm_client = ResourceManagementClient(azure_credential, azure_subscription)
    destination_resource_group = arm_client.resource_groups.get(destination_rg)
    resources = [
        resource for resource in arm_client.resources.list_by_resource_group(source_rg)
        if resource.name in resources_to_move
    ]
    resource_ids = [resource.id for resource in resources]
    logger.info(f"Validation resource list: {resource_ids}")
    if not resource_ids:
        logger.info("The list of resources in move definition cannot be null or empty")
        return CommandResponse.fail()
    resource_group_id = f"/subscriptions/{azure_subscription}/resourcegroups/{destination_rg}"
    role_assign_id = set_contributor_role(azure_subscription=azure_subscription,
                                          resource_group_id=resource_group_id,
                                          context_id=context_id,
                                          source=source,
                                          destination=destination)
    validate_move_resources_result = arm_client.resources.begin_validate_move_resources(
        source_rg, {
            "resources": resource_ids,
            "target_resource_group": destination_resource_group.id
        })
    validate_move_resources_result.wait()
    if validate_move_resources_result.done():
        result = validate_move_resources_result.result()
        if result is None:
            logger.info(f"Moving resource list: {resource_ids}")
            poller = arm_client.resources.begin_move_resources(source_rg, {
                "resources": resource_ids,
                "target_resource_group": destination_resource_group.id
            })
            poller.wait()
            if poller.done():
                logger.info("Successfully moved")
    remove_contributor_role(azure_subscription=azure_subscription,
                            resource_group_id=resource_group_id,
                            role_assign_id=role_assign_id,
                            context_id=context_id,
                            destination=destination)
    return CommandResponse.success()


def set_contributor_role(azure_subscription: str, resource_group_id: str, context_id: str, source: str,
                         destination: str):
    baby_client_id_dest = env.configuration.get_var(resource_id="babylon",
                                                    var_name="client_id",
                                                    context_id=context_id,
                                                    environ_id=destination)
    authorization_client = AuthorizationManagementClient(
        credential=get_azure_credentials(baby_client_id=baby_client_id_dest,
                                         context_id=context_id,
                                         environ_id=destination),
        subscription_id=azure_subscription,
    )
    roles = list(
        authorization_client.role_definitions.list(resource_group_id, filter="roleName eq '{}'".format("Contributor")))
    assert len(roles) == 1
    role_assign_id = uuid.uuid4()
    baby_sp_id_source = env.configuration.get_var(resource_id="babylon",
                                                  var_name="principal_id",
                                                  context_id=context_id,
                                                  environ_id=source)
    try:
        authorization_client.role_assignments.create(resource_group_id, role_assign_id, {
            "role_definition_id": roles[0].id,
            "principal_id": baby_sp_id_source
        })
    except Exception as e:
        logger.error(f"Failed to assign a new role: {e}")
    return role_assign_id


def remove_contributor_role(azure_subscription: str, resource_group_id: str, role_assign_id: str, context_id: str,
                            destination: str):
    baby_client_id_dest = env.configuration.get_var(resource_id="babylon",
                                                    var_name="client_id",
                                                    context_id=context_id,
                                                    environ_id=destination)
    authorization_client = AuthorizationManagementClient(
        credential=get_azure_credentials(baby_client_id=baby_client_id_dest,
                                         context_id=context_id,
                                         environ_id=destination),
        subscription_id=azure_subscription,
    )
    try:
        authorization_client.role_assignments.delete(resource_group_id, role_assign_id)
    except Exception as e:
        logger.error(f"Failed to assign a new role: {e}")
    return True
