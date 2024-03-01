import logging
import jmespath

from typing import Optional
from azure.digitaltwins.core import DigitalTwinsClient
from click import command
from click import option
from Babylon.utils.decorators import timing_decorator, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_adt_client

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_adt_client
@option("--filter", "filter", help="Filter response with a jmespath query")
def get_all(adt_client: DigitalTwinsClient, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all models id from ADT
    """
    models = adt_client.list_models(include_model_definition=True)
    output_data = [model.as_dict() for model in models]
    if len(output_data) and filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
