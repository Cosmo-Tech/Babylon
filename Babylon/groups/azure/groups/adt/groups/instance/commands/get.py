import json
import logging
import pathlib
from typing import Optional

import click
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from rich.pretty import Pretty

from ........utils.api import convert_keys_case
from ........utils.api import underscore_to_camel
from ........utils.decorators import require_platform_key
from ........utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")

pass_digital_twins_client = make_pass_decorator(AzureDigitalTwinsManagementClient)


@command()
@pass_digital_twins_client
@timing_decorator
@require_platform_key("resource_group_name")
@option(
    "-o",
    "--output_file",
    "output_file",
    type=click.Path(writable=True),
    help="The path to the file where the retrieved ADT instance details should be outputted (json-formatted)",
)
@argument("adt_instance_name")
def get(
    digital_twins_client: AzureDigitalTwinsManagementClient,
    resource_group_name: str,
    adt_instance_name: str,
    output_file: Optional[str] = None,
):
    """Get an azure digital twins instance details"""
    try:
        instance = digital_twins_client.digital_twins.get(resource_group_name, adt_instance_name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Failed to create ADT instance '{adt_instance_name}': {error_message[0]}")
        return
    instance = instance.as_dict()
    instance.remove("id")

    if not output_file:
        logger.info(Pretty(instance))
        return

    _instances_to_dump = convert_keys_case(instance, underscore_to_camel)
    with open(output_file, "w") as _file:
        json.dump(_instances_to_dump, _file, ensure_ascii=False)
    logger.info(f"Full content was dumped on {output_file}")
