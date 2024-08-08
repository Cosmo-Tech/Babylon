import logging

from click import argument, command
from hvac import Client
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command(help="KEY_VALUE: The key-value pair to add or update, in the format key=value")
@injectcontext()
@pass_hvac_client
@argument("organization_id", type=str)
@argument("workspace_key", type=str)
@argument("cluster_name", type=str)
@argument("key_value", type=str)
def set_workspace_secrets(hvac_client: Client, organization_id: str, workspace_key: str, cluster_name: str,
                          key_value: str) -> CommandResponse:
    """
    Set a secret in workspaces scope
    """
    org_tenant = f"{env.organization_name}/{env.tenant_id}"
    secret_path = f"{org_tenant}/clusters/{cluster_name}/{env.environ_id}/workspaces/{organization_id}-{workspace_key}"
    key, value = key_value.split('=', 1)
    existing_secrets = hvac_client.read(path=secret_path)
    if existing_secrets:
        secrets = existing_secrets['data']
        secrets[key] = value
    else:
        secrets = {f"{key}": value}

    hvac_client.write(path=secret_path, **secrets)
    logger.info("[vault] successfully add workspace secret")
    return CommandResponse.success()
