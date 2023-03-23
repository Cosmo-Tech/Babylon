import logging
from typing import Optional
import jmespath

from azure.digitaltwins.core import DigitalTwinsClient
from click import command
from click import option

from .....utils.decorators import timing_decorator
from .....utils.decorators import output_to_file
from .....utils.response import CommandResponse
from .....utils.clients import pass_adt_client

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@pass_adt_client
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get_all(adt_client: DigitalTwinsClient, filter: Optional[str] = None) -> CommandResponse:
    """Get all models id from ADT"""
    models = adt_client.list_models(include_model_definition=True)
    output_data = [model.as_dict() for model in models]
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
