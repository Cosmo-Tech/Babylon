import json
import logging
import pathlib
import pprint

import click
from azure.core.exceptions import ResourceExistsError
from azure.core.exceptions import ResourceNotFoundError
from azure.digitaltwins.core import DigitalTwinsClient
from click import argument
from click import command
from click import make_pass_decorator
from click import option

from ........utils.decorators import allow_dry_run

logger = logging.getLogger("Babylon")

pass_dt_client = make_pass_decorator(DigitalTwinsClient)


def upload_one_model(dt_client: DigitalTwinsClient, model: dict, override: bool, dry_run: bool) -> bool:
    """ Send only one model to the ADT
    :param dt_client: DigitalTwinsClient instance used to send the model
    :param model: dict object containing the model
    :param override: Should the model be overridden if it exists ?
    :param dry_run: are we in dry run mode ?
    :return: True if the model was uploaded
    """
    try:
        model_id = model["@id"]
    except KeyError:
        logger.error("Given model is missing `@id`")
        return False

    if override:
        logger.info(f"Deleting model {model_id}")
        if not dry_run:
            try:
                _ = dt_client.get_model(model_id)
                dt_client.delete_model(model_id)
            except ResourceNotFoundError:
                pass

    logger.info(f"Uploading model {model_id}")
    logger.debug(pprint.pformat(model))

    if not dry_run:
        try:
            dt_client.create_models([
                model,
            ])
        except ResourceExistsError:
            logger.error(f"Model {model_id} already exists")
            return False
    return True


@command()
@pass_dt_client
@argument("model_file",
          type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
@option("-o", "--override", "override_if_exists", is_flag=True, help="Override existing models")
@allow_dry_run
def upload(dt_client: DigitalTwinsClient, model_file: pathlib.Path, override_if_exists: bool = False, dry_run: bool = False):
    """Upload MODEL_FILE to adt

    MODEL_FILE must be a json file"""

    if model_file.suffix != ".json":
        logger.error(f"{model_file} is not a json file")
        return

with open(model_file, "r')) as file:
    model_file_content = json.load(file)

    if type(model_file_content) is list:
        for model in model_file_content:
            upload_one_model(dt_client, model, override_if_exists, dry_run)
    else:
        upload_one_model(dt_client, model_file_content, override_if_exists, dry_run)
