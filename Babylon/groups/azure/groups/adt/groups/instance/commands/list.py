import json
import logging
import pathlib
from pprint import pformat
from typing import Optional

import click
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import command
from click import make_pass_decorator
from click import option

from ........utils.api import convert_keys_case
from ........utils.api import filter_api_response
from ........utils.api import underscore_to_camel
from ........utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")

pass_digital_twins_client = make_pass_decorator(AzureDigitalTwinsManagementClient)


@command()
@pass_digital_twins_client
@require_platform_key("resource_group_name", "resource_group_name")
@option(
    "-o",
    "--output_file",
    "output_file",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="Write full output of the adt api in target file",
)
@option(
    "-f",
    "--fields",
    "fields",
    required=False,
    type=str,
    help="Fields witch will be keep in response data, by default all",
)
def list(
    digital_twins_client: AzureDigitalTwinsManagementClient,
    resource_group_name: str,
    output_file: Optional[pathlib.Path],
    fields: Optional[str] = None,
):
    """Get all azure digital twins instances"""

    instances = digital_twins_client.digital_twins.list_by_resource_group(resource_group_name)
    instances = [_ele.as_dict() for _ele in instances]
    for ele in instances:
        del ele["id"]

    if fields:
        fields = fields.replace(" ", "").split(",")
        instances = filter_api_response(instances, fields)

    if output_file:
        _instances_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in instances]
        with open(output_file, "w") as _file:
            json.dump(_instances_to_dump, _file, ensure_ascii=False)
        logger.info("Full content was dumped on %s", output_file)
        return

    logger.info(pformat(instances))
