import logging
from typing import Optional
import jmespath

from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import command
from click import option

from .....utils.decorators import require_platform_key
from .....utils.decorators import output_to_file
from .....utils.decorators import timing_decorator
from .....utils.response import CommandResponse
from .....utils.clients import pass_adt_management_client

logger = logging.getLogger("Babylon")


@command()
@pass_adt_management_client
@timing_decorator
@require_platform_key("resource_group_name")
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get_all(
    adt_management_client: AzureDigitalTwinsManagementClient,
    resource_group_name: str,
    filter: Optional[str] = None,
) -> CommandResponse:
    """Get all azure digital twins instances"""
    try:
        instances = adt_management_client.digital_twins.list_by_resource_group(resource_group_name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Cannot retrieve ADT instances list : {error_message[0]}")
        return CommandResponse.fail()

    instances = [_ele.as_dict() for _ele in instances]

    if filter:
        instances = jmespath.search(filter, instances)

    return CommandResponse.success(instances, verbose=True)
