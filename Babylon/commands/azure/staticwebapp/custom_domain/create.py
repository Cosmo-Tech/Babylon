import logging
import pathlib

from typing import Any, Optional
from click import command
from click import argument
from click import Path
from click import option
from Babylon.commands.azure.staticwebapp.custom_domain.service.api import (
    AzureSWACustomDomainService,
)
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option(
    "--file",
    "create_file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    help="Your custom custom-domain description file yaml",
)
@argument("webapp_name", type=QueryType())
@argument("domain_name", type=QueryType())
@inject_context_with_resource({"azure": ["resource_group_name", "subscription_id"]})
def create(
    context: Any,
    azure_token: str,
    webapp_name: str,
    domain_name: str,
    create_file: Optional[str] = None,
) -> CommandResponse:
    """
    Create a static webapp custom domain in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site-custom-domain
    """
    api_swa_custom_domain = AzureSWACustomDomainService(azure_token=azure_token, state=context)
    response = api_swa_custom_domain.upsert(
        webapp_name=webapp_name,
        domain_name=domain_name,
        create_file=create_file,
    )
    return CommandResponse.success(response, verbose=True)
