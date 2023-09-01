import logging
import pathlib

from typing import Any, Optional
from click import command
from click import argument
from click import option
from click import pass_context
from click import Context
from click import Path
from .create import create
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_context
@pass_azure_token()
@option("--file", "create_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@argument("webapp_name", type=QueryType())
@argument("domain_name", type=QueryType())
@inject_context_with_resource({'azure': ['resource_group_name']})
def update(
    ctx: Context,
    context: Any,
    azure_token: str,
    webapp_name: str,
    domain_name: str,
    create_file: Optional[str] = None,
) -> CommandResponse:
    """
    Update a static webapp custom domain in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    return ctx.forward(create)
