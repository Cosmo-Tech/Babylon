import json
import logging
import pathlib
from typing import Optional

import click
from azure.digitaltwins.core import DigitalTwinsClient
from azure.digitaltwins.core import DigitalTwinsModelData
from click import command
from click import option

from .....utils.decorators import timing_decorator
from .....utils.response import CommandResponse
from .....utils.clients import pass_adt_client

logger = logging.getLogger("Babylon")


@command()
@pass_adt_client
@option(
    "-o",
    "--output-file",
    "output_file",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="Write full output of the adt api in target file",
)
@timing_decorator
def list(adt_client: DigitalTwinsClient, output_file: Optional[pathlib.Path] = None) -> CommandResponse:
    """List all models id from ADT"""
    if output_file and output_file.suffix != ".json":
        logger.error(f"{output_file} is not a json file")
        return CommandResponse.fail()

    data = adt_client.list_models(include_model_definition=True)

    logger.info("Listing all model ids :")

    _file_content = []
    for model in data:
        model: DigitalTwinsModelData
        logger.info(f"  - {model.as_dict()['model']['@id']}")
        if output_file:
            _file_content.append(model.as_dict())

    if output_file:
        logger.info(f"Writing models to {output_file.absolute()}")
        json.dump(_file_content, open(output_file, "w"))
    return CommandResponse.success({"models": data})