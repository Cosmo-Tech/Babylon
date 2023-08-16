import logging
import jmespath

from typing import Any, Optional
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import command
from click import option
from Babylon.utils.decorators import output_to_file, wrapcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.clients import pass_adt_management_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_adt_management_client
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({'azure': ['resource_group_name']})
def get_all(
    context: Any,
    adt_management_client: AzureDigitalTwinsManagementClient,
    filter: Optional[str] = None,
) -> CommandResponse:
    """
    Get all azure digital twins instances
    """
    resource_group_name = context['azure_resource_group_name']
    try:
        instances = adt_management_client.digital_twins.list_by_resource_group(resource_group_name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Cannot retrieve ADT instances list : {error_message[0]}")
        return CommandResponse.fail()
    instances = [_ele.as_dict() for _ele in instances]
    if len(instances) and filter:
        instances = jmespath.search(filter, instances)
    return CommandResponse.success(instances, verbose=True)
