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

logger = logging.getLogger("Babylon")

pass_dt_client = make_pass_decorator(DigitalTwinsClient)


def upload_one_model(dt_client: DigitalTwinsClient, model: dict, override: bool) -> bool:
    """
    Send only one model to the ADT
    :param dt_client: DigitalTwinsClient instance used to send the model
    :param model: dict object containing the model
    :param override: Should the model be overridden if it exists ?
    :return: True if the model was uploaded
    """
    try:
        model_id = model['@id']
    except KeyError:
        logger.error("Given model is missing `@id`")
        return False

    if override:
        try:
            m = dt_client.get_model(model_id)
            logger.info(f"Deleting model `{model_id}`")
            dt_client.delete_model(model_id)
        except ResourceNotFoundError:
            pass

    logger.info(f"Uploading model `{model_id}`")
    logger.debug(pprint.pformat(model))

    try:
        dt_client.create_models([model, ])
    except ResourceExistsError:
        logger.error(f"Model `{model_id}` already exists")
        return False
    return True


@command()
@pass_dt_client
@argument("model_file", type=click.Path(exists=True,
                                        file_okay=True,
                                        dir_okay=False,
                                        readable=True,
                                        path_type=pathlib.Path))
@option("-o", "--override", "override_if_exists", is_flag=True, help="Override existing models")
def upload_model(dt_client: DigitalTwinsClient, model_file: pathlib.Path, override_if_exists: bool):
    """Upload MODEL_FILE to adt"""

    model_file_content = json.load(open(model_file, 'r'))

    if type(model_file_content) is list:
        for model in model_file_content:
            upload_one_model(dt_client, model, override_if_exists)
    else:
        upload_one_model(dt_client, model_file_content, override_if_exists)
