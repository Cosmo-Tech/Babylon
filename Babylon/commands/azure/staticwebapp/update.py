import logging
import pathlib
from typing import Optional

from click import command
from click import argument
from click import option
from click import pass_context
from click import Context
from click import Path

from .create import create
from ....utils.credentials import pass_azure_token
from ....utils.decorators import require_platform_key
from ....utils.response import CommandResponse
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_context
@pass_azure_token()
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@argument("webapp_name", type=QueryType())
@option("-f", "--file", "swa_file", type=Path(readable=True, dir_okay=False, path_type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)))
def update(ctx: Context,
           azure_token: str,
           azure_subscription: str,
           resource_group_name: str,
           webapp_name: str,
           swa_file: Optional[Path] = None) -> CommandResponse:
    """
    Update a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    return ctx.forward(create)
