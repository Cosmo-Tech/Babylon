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
from .....utils.decorators import require_platform_key
from .....utils.response import CommandResponse
from .....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("azure_subscription")
@require_platform_key("resource_group_name")
@argument("webapp_name", type=QueryType())
@argument("domain_name", type=QueryType())
@option("-f", "--file", "create_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
def update(ctx: Context,
           azure_subscription: str,
           resource_group_name: str,
           webapp_name: str,
           domain_name: str,
           create_file: Optional[str] = None,
           use_working_dir_file: bool = False) -> CommandResponse:
    """
    Update a static webapp custom domain in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    return ctx.forward(create)
