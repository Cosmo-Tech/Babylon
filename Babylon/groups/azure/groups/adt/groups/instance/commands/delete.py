import logging
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import argument
from click import command
from click import confirm
from click import make_pass_decorator
from click import option
from click import prompt

from ........utils.decorators import require_platform_key
from ........utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")

pass_digital_twins_client = make_pass_decorator(AzureDigitalTwinsManagementClient)


@command()
@timing_decorator
@pass_digital_twins_client
@argument("adt_instance_name")
@require_platform_key("resource_group_name")
@option("-f", "--force", "force_validation", is_flag=True, help="Don't ask for validation before delete")
def delete(digital_twins_client: AzureDigitalTwinsManagementClient,
           resource_group_name: str,
           adt_instance_name: str,
           force_validation: Optional[bool] = False) -> Optional[str]:
    """Delete a ADT instance in current platform resource group"""

    if not force_validation:
        if not confirm(f"You are trying to delete adt resource {adt_instance_name} \nDo you want to continue ?"):
            logger.info("Adt instance deletion aborted.")
            return

        confirm_adt_instance_name = prompt("Confirm Adt instance name")
        if confirm_adt_instance_name != adt_instance_name:
            logger.error("Wrong Adt instance name , "
                         "the id must be the same as the one that has been provide in delete command argument")
            return

    logger.info(f"Deleting Adt instance {adt_instance_name}")
    try:
        poller = digital_twins_client.digital_twins.begin_delete(resource_group_name, adt_instance_name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Failed to create ADT instance '{adt_instance_name}': {error_message[0]}")
        return

    # Long-running operations return a poller object; calling poller.result()
    # waits for completion.
    adt_deletion_result = poller.result()
    logger.info(f"Deleted digital twins instance {adt_deletion_result.name}")
    return adt_deletion_result.name
