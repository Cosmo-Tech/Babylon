import os
from click import group
from click import pass_context
from click.core import Context
from azure.containerregistry import ContainerRegistryClient
from Babylon.utils.decorators import require_deployment_key
from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
@require_deployment_key("acr_registry_name", "acr_registry_name")
def acr(ctx: Context, acr_registry_name: str):
    """Group initialized from a template"""
    # Login to registry
    os.system(f"az acr login --name {acr_registry_name}")
    ctx.obj = ContainerRegistryClient(
        f"https://{acr_registry_name}.azurecr.io",
        ctx.parent.obj,
        audience="https://management.azure.com")

for _command in list_commands:
    acr.add_command(_command)

for _group in list_groups:
    acr.add_command(_group)
