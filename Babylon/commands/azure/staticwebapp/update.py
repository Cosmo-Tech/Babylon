import logging
import pathlib

from click import command
from click import argument
from click import option
from click import pass_context
from click import Context
from click import Path

from .create import create
from ....utils.decorators import require_platform_key
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@argument("webapp_name")
@option("-f", "--file", "create_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path), required=True)
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
def update(ctx: Context,
           azure_subscription: str,
           resource_group_name: str,
           webapp_name: str,
           create_file: str,
           use_working_dir_file: bool = False) -> CommandResponse:
    """
    Update a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    return ctx.forward(create)
