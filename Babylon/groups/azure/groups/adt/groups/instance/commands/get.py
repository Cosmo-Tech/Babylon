import json
import logging
import pathlib
from pprint import pformat
from typing import Optional

import click
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import argument
from click import command
from click import option

from ........utils.api import convert_keys_case
from ........utils.api import underscore_to_camel
from ........utils.decorators import require_platform_key
from ........utils.decorators import timing_decorator
from ........utils.response import CommandResponse
from ........utils.clients import pass_adt_management_client

logger = logging.getLogger("Babylon")


@command()
@pass_adt_management_client
@timing_decorator
@require_platform_key("resource_group_name", "resource_group_name")
@option(
    "-o",
    "--output_file",
    "output_file",
    type=click.Path(),
    help="The path to the file where the retrieved ADT instance details should be outputted (json-formatted)",
)
@argument("adt_instance_name")
def get(
    adt_management_client: AzureDigitalTwinsManagementClient,
    resource_group_name: str,
    adt_instance_name: str,
    output_file: Optional[pathlib.Path],
) -> CommandResponse:
    """Get an azure digital twins instance details"""
    try:
        instance = adt_management_client.digital_twins.get(resource_group_name, adt_instance_name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Failed to create ADT instance '{adt_instance_name}': {error_message[0]}")
        return CommandResponse.fail()
    instance = instance.as_dict()
    del instance["id"]

    if output_file:
        _instances_to_dump = convert_keys_case(instance, underscore_to_camel)
        with open(output_file, "w") as _file:
            json.dump(_instances_to_dump, _file, ensure_ascii=False)
        logger.info("Full content was dumped on %s", output_file)

    logger.info(pformat(instance))
    return CommandResponse.success(instance)
