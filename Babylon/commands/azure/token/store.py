import logging

from typing import Any
from click import Choice, command, option
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from azure.identity import TokenCachePersistenceOptions
from azure.identity import InteractiveBrowserCredential
from azure.identity import AuthenticationRecord

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@option("--email", "email", help="User email")
@option("--scope", "scope", type=Choice(['default', "powerbi", "graph"]), required=True)
@inject_context_with_resource({'azure': ['user_principal_id', 'cli_client_id']})
def store(context: Any, scope: str, email: str) -> CommandResponse:
    """
    Store a refresh token using a secret key
    """
    home_account_id = context['azure_user_principal_id']
    cli_client_id = context['azure_cli_client_id']
    email = email or env.configuration.get_var(resource_id="azure", var_name="email")
    cpo = TokenCachePersistenceOptions(allow_unencrypted_storage=True)
    record = {
        "authority": "login.microsoftonline.com",
        "clientId": cli_client_id,
        "homeAccountId": f"{home_account_id}.{env.tenant_id}",
        "tenantId": env.tenant_id,
        "username": email,
        "version": "1.0"
    }

    record_deserialize = AuthenticationRecord.deserialize(str(record).replace("'", '"'))
    credential = InteractiveBrowserCredential(
        cache_persistence_options=cpo,
        authentication_record=record_deserialize,
        redirect_uri="http://localhost:8484",
    )

    env.AZURE_SCOPES.update({"csm_api": env.configuration.get_var(resource_id="api", var_name="scope")})
    env.AZURE_SCOPES.update({"powerbi": env.configuration.get_var(resource_id="powerbi", var_name="scope")})

    token = credential._request_token(f"{env.AZURE_SCOPES[scope]} offline_access")
    env.working_dir.generate_secret_key()
    if "refresh_token" in token:
        token_encrypt = env.working_dir.encrypt_content(env.working_dir.encoding_key,
                                                        bytes(token['refresh_token'], encoding="utf-8"))

        env.set_users_secrets(email, scope, dict(token=token_encrypt.decode("utf-8")))
    return CommandResponse.success()
