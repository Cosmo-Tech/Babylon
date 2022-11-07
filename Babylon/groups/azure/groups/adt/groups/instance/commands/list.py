import json
import logging
import pathlib
from typing import Optional

import click
from azure.core.exceptions import HttpResponseError
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import command
from click import make_pass_decorator
from click import option
from rich.pretty import Pretty

from ........utils.api import convert_keys_case
from ........utils.api import filter_api_response
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
    "--output-file",
    "output_file",
    type=click.Path(writable=True),
    help="The path to the file where ADT instances details should be outputted (json-formatted)",
)
@option(
    "-f",
    "--fields",
    "fields",
    type=str,
    help="Fields witch will be keep in response data, by default all",
)
def list(
    digital_twins_client: AzureDigitalTwinsManagementClient,
    resource_group_name: str,
    output_file: Optional[str] = None,
    fields: Optional[str] = None,
):
    """Get all azure digital twins instances"""
    try:
        instances = digital_twins_client.digital_twins.list_by_resource_group(resource_group_name)
    except HttpResponseError as _http_error:
        error_message = _http_error.message.split("\n")
        logger.error(f"Cannot retrieve ADT instances list : {error_message[0]}")
        return

    instances = [_ele.as_dict() for _ele in instances]

    if fields:
        fields = fields.replace(" ", "").split(",")
        instances = filter_api_response(instances, fields)

    if not output_file:
        logger.info(Pretty(instances))
        return

    _instances_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in instances]
    with open(output_file, "w") as _file:
        json.dump(_instances_to_dump, _file, ensure_ascii=False)
    logger.info("Full content was dumped on %s", output_file)
    return
