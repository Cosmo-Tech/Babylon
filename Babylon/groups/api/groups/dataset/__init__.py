from click import group
from click import pass_context
from click.core import Context
from cosmotech_api import ApiClient
from cosmotech_api.api.dataset_api import DatasetApi

from .....utils.decorators import pass_api_configuration
from .commands import list_commands
from .groups import list_groups


@group()
@pass_api_configuration
@pass_context
def dataset(ctx: Context, api_configuration):
    """Subgroup handling Datasets in the cosmotech API"""
    api_client = ApiClient(api_configuration)
    ctx.obj = DatasetApi(api_client)


for _command in list_commands:
    dataset.add_command(_command)

for _group in list_groups:
    dataset.add_command(_group)
