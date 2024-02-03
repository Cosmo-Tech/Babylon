from Babylon.utils.environment import Environment
from azure.identity import TokenCachePersistenceOptions
from azure.identity import InteractiveBrowserCredential
from azure.identity import AuthenticationRecord

env = Environment()


class AzureTokenService:

    def __init__(self, context: dict = None) -> None:
        self.context = context

    def get(self, email: str, scope: str):
        email = email or env.configuration.get_var(
            resource_id="azure", var_name="email"
        )
        access_token = env.get_access_token_with_refresh_token(
            username=email, internal_scope=scope
        )
        return access_token

    def store(self, email: str, scope: str):
        home_account_id = self.context["azure_user_principal_id"]
        cli_client_id = self.context["azure_cli_client_id"]
        email = email or env.configuration.get_var(
            resource_id="azure", var_name="email"
        )
        cpo = TokenCachePersistenceOptions(allow_unencrypted_storage=True)
        record = {
            "authority": "login.microsoftonline.com",
            "clientId": cli_client_id,
            "homeAccountId": f"{home_account_id}.{env.tenant_id}",
            "tenantId": env.tenant_id,
            "username": email,
            "version": "1.0",
        }

        record_deserialize = AuthenticationRecord.deserialize(
            str(record).replace("'", '"')
        )
        credential = InteractiveBrowserCredential(
            cache_persistence_options=cpo,
            authentication_record=record_deserialize,
            redirect_uri="http://localhost:8484",
        )

        env.AZURE_SCOPES.update(
            {"csm_api": env.configuration.get_var(resource_id="api", var_name="scope")}
        )
        env.AZURE_SCOPES.update(
            {
                "powerbi": env.configuration.get_var(
                    resource_id="powerbi", var_name="scope"
                )
            }
        )
        token = credential._request_token(f"{env.AZURE_SCOPES[scope]} offline_access")
        env.working_dir.generate_secret_key()
        if "refresh_token" in token:
            token_encrypt = env.working_dir.encrypt_content(
                env.working_dir.encoding_key,
                bytes(token["refresh_token"], encoding="utf-8"),
            )

            env.set_users_secrets(
                email, scope, dict(token=token_encrypt.decode("utf-8"))
            )
