import yaml
import shutil
import tempfile
import logging
import pathlib

from Babylon.utils.clients import pass_arm_client
from click import Path, argument, command, option
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import timing_decorator, wrapcontext
from azure.mgmt.resource import ResourceManagementClient

logger = logging.getLogger('Babylon')


@command()
@wrapcontext()
@pass_arm_client
@argument("resource_group")
@option("--item", "items", multiple=True)
@option("--resources-file",
        "resources_file",
        type=Path(path_type=pathlib.Path, exists=True),
        help="File contains list of resources to move")
@timing_decorator
def check(arm_client: ResourceManagementClient, resource_group: str, resources_file: pathlib.Path,
          items: list) -> CommandResponse:
    """
    Check resource exists in resource group
    """
    resources_to_move = list()
    if resources_file and resources_file.exists():
        if resources_file.suffix in [".json"]:
            logger.error("json file not supported")
            return CommandResponse.fail()
        resources_to_move = yaml.load(resources_file.open("r"), Loader=yaml.SafeLoader)
    _items = list(map(lambda x: {"name": x}, items))
    resources_to_move = resources_to_move + _items
    resources_to_move = [i.get('name') for i in resources_to_move]
    resources = [
        resource for resource in arm_client.resources.list_by_resource_group(resource_group)
        if resource.name in resources_to_move
    ]
    resource_ids = [resource.name for resource in resources]
    data = []
    for item in resources_to_move:
        data.append({"name": item, "exist": item in resource_ids})
    yaml_file = yaml.dump(data)
    tmpf = tempfile.NamedTemporaryFile(mode="w+")
    tmpf.write(yaml_file)
    tmpf.seek(0)
    resources_file = resources_file or f".payload/resources.{resource_group}.yaml"
    shutil.copy(tmpf.name, resources_file)
    tmpf.flush()
    tmpf.close()
    logger.info(f"Check list dumped in : {resources_file}")
    return CommandResponse.success()
