import logging
import pathlib

from typing import Any, Optional
from click import command
from click import argument
from click import option
from click import Path

from Babylon.commands.azure.staticwebapp.custom_domain.service.api import AzureSWACustomDomainService
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_azure_token()
@option("--file",
        "create_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        help="Your custom custom-domain description file yaml")
@argument("webapp_name", type=QueryType())
@argument("domain_name", type=QueryType())
@retrieve_state
def update(
    state: Any,
    azure_token: str,
    webapp_name: str,
    domain_name: str,
    create_file: Optional[str] = None,
) -> CommandResponse:
    """
    Update a static webapp custom domain in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    service = AzureSWACustomDomainService(azure_token=azure_token, state=state)
    response = service.upsert(
        webapp_name=webapp_name,
        domain_name=domain_name,
        create_file=create_file,
    )
    return CommandResponse.success(response, verbose=True)
