import json
import logging
import pathlib
import pprint
from typing import Optional

import click
from azure.digitaltwins.core import DigitalTwinsClient
from azure.digitaltwins.core import DigitalTwinsModelData
from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient
from click import command
from click import make_pass_decorator
from click import option

logger = logging.getLogger("Babylon")

pass_dt_client = make_pass_decorator(DigitalTwinsClient)


@command()
@pass_dt_client
@option(
    "-o",
    "--output_file",
    "output_file",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="Write full output of the adt api in target file",
)
def list(client: DigitalTwinsClient, output_file: Optional[pathlib.Path]):
    """Get all azure digital twins inatnces"""
    
    
