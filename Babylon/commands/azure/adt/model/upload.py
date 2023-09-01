import glob
import json
import logging
import pathlib
import pprint

from click import Path
from click import argument
from click import command
from click import option
from azure.core.exceptions import ResourceExistsError
from azure.core.exceptions import ResourceNotFoundError
from azure.digitaltwins.core import DigitalTwinsClient
from Babylon.utils.decorators import describe_dry_run, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_adt_client

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@pass_adt_client
@option("--override", "override_if_exists", is_flag=True, help="Override existing models")
@describe_dry_run("Would go through the given file and upload the models to ADT")
@argument("model_file_folder",
          type=Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=pathlib.Path))
def upload(
    adt_client: DigitalTwinsClient,
    model_file_folder: pathlib.Path,
    override_if_exists: bool = False,
):
    """
    Upload MODEL_FILE_FOLDER content to adt
    """

    model_files = glob.glob(str(model_file_folder / "*.json"))
    if not len(model_files):
        return CommandResponse.fail()

    for _model_file in model_files:
        model_file = pathlib.Path(_model_file)
        if model_file.suffix != ".json":
            logger.error(f"{model_file} is not a json file")
            continue

        with open(model_file, "r") as file:
            model_file_content = json.load(file)

        if isinstance(model_file_content, list):
            for model in model_file_content:
                upload_one_model(adt_client, model, override_if_exists)
            continue
        upload_one_model(adt_client, model_file_content, override_if_exists)
    return CommandResponse.success()


def upload_one_model(adt_client: DigitalTwinsClient, model_file_content: dict, override: bool) -> bool:
    """ Send only one model to the ADT
    :param dt_client: DigitalTwinsClient instance used to send the model
    :param model: dict object containing the model
    :param override: Should the model be overridden if it exists ?
    :return: True if the model was uploaded
    """
    if override:
        for model in model_file_content:
            if 'extends' in model:
                temp = model["extends"]
                for item in temp:
                    print(item)
                    logger.info(f"Deleting model {item}")
                    try:
                        _ = adt_client.get_model(item)
                        adt_client.delete_model(item)
                    except ResourceNotFoundError:
                        pass
        for model1 in model_file_content:
            try:
                model_id = model1["@id"]
            except KeyError:
                logger.error("Given model is missing `@id`")
                return False

            logger.info(f"Deleting model {model_id}")
            try:
                _ = adt_client.get_model(model_id)
                adt_client.delete_model(model_id)
            except ResourceNotFoundError:
                pass

    logger.info("Uploading model")
    logger.debug(pprint.pformat(model_file_content))

    try:
        adt_client.create_models(model_file_content, )
    except ResourceExistsError:
        logger.error("Model already exists")
        return False
    return True
