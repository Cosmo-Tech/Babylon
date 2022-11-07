import glob
import json
import logging
import pathlib

import click
from azure.core.exceptions import ResourceExistsError
from azure.core.exceptions import ResourceNotFoundError
from azure.digitaltwins.core import DigitalTwinsClient
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from rich.pretty import Pretty

from ........utils.decorators import describe_dry_run

logger = logging.getLogger("Babylon")

pass_dt_client = make_pass_decorator(DigitalTwinsClient)


def upload_one_model(dt_client: DigitalTwinsClient, model: dict, override: bool) -> bool:
    """ Send only one model to the ADT
    :param dt_client: DigitalTwinsClient instance used to send the model
    :param model: dict object containing the model
    :param override: Should the model be overridden if it exists ?
    :return: True if the model was uploaded
    """
    model_id = model.get("@id")
    if not model_id:
        logger.error("Given model is missing `@id`")
        return False

    if override:
        logger.info(f"Deleting model {model_id}")
        try:
            _ = dt_client.get_model(model_id)
            dt_client.delete_model(model_id)
        except ResourceNotFoundError:
            pass

    logger.info(f"Uploading model {model_id}")
    logger.debug(Pretty(model))

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
@argument("model_file_folder",
          type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=pathlib.Path))
@option("-o", "--override", "override_if_exists", is_flag=True, help="Override existing models")
@describe_dry_run("Would go through the given file and upload the models to ADT")
def upload(
    dt_client: DigitalTwinsClient,
    model_file_folder: pathlib.Path,
    override_if_exists: bool = False,
):
    """Upload MODEL_FILE_FOLDER content to adt

    MODEL_FILE_FOLDER must be a folder containing json file"""

    model_files = glob.glob(str(model_file_folder / "*.json"))
    for _model_file in model_files:
        model_file = pathlib.Path(_model_file)
        if model_file.suffix != ".json":
            logger.error(f"{model_file} is not a json file")
            continue

        with open(model_file, "r") as file:
            model_file_content = json.load(file)

        if isinstance(model_file_content, list):
            for model in model_file_content:
                upload_one_model(dt_client, model, override_if_exists)
            continue

        upload_one_model(dt_client, model_file_content, override_if_exists)
