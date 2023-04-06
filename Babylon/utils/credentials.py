import logging
from functools import wraps
from typing import Any
from typing import Callable

from azure.core.credentials import TokenCredential
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import (
    ChainedTokenCredential, 
    ManagedIdentityCredential, 
    InteractiveBrowserCredential, 
    TokenCachePersistenceOptions,
    SharedTokenCacheCredential,
    DefaultAzureCredential,
    AuthenticationRecord
    )
from azure.identity._internal import within_credential_chain
from .environment import Environment

logger = logging.getLogger("Babylon")


def get_azure_token(scope: str = "default") -> str:
    """Returns an azure token"""
    # Getting scope url from utils.scope
    SCOPES = {
        "graph": "https://graph.microsoft.com/.default",
        "default": "https://management.azure.com/.default",
        "powerbi": Environment().configuration.get_deploy_var("powerbi_api_scope"),
        "csm_api": Environment().configuration.get_platform_var("api_scope")
    }
    credentials = get_azure_credentials()
    scope_url = SCOPES[scope.lower()]
    logger.debug(f"Getting azure token with scope {scope_url}")
    try:
        token = credentials.get_token(scope_url)
    except ClientAuthenticationError:
        logger.error(f"Could not get token with scope {scope_url}")
        raise ConnectionError(f"Could not connect to Azure API with scope {scope_url}")
    return token.token


def get_azure_credentials() -> Any:
    """Logs to Azure and saves the token as a config variable"""
    env = Environment()
    azure_tenant_id = env.configuration.get_platform_var("azure_tenant_id")
    azure_client_id = env.configuration.get_platform_var("azure_client_id")
    cached_credentials = env.convert_data_query("%secrets%azure")
    redirect_uri_port = env.configuration.get_platform_var("redirect_uri") or "8842"
    redirect_uri = f"http://localhost:{redirect_uri_port}"

    fn = "cred_cache.txt"
    deserialized_record = None
    import os, json
    # if os.path.exists(fn):
    #     # read serialized authentication_record from local file
    #     with open(fn, "rt") as infile:
    #         cred_json = infile.read()
    #         deserialized_record = AuthenticationRecord.deserialize(cred_json)

    cred_json = env.working_dir.get_file_content(".secrets.yaml.encrypt")
    logger.info(type(cred_json))
    if cred_json.get("babylon"):
        deserialized_record = AuthenticationRecord.deserialize(str(cred_json.get("babylon")).replace("\'", "\""))

    cpo = TokenCachePersistenceOptions(allow_unencrypted_storage=True)
    credential = InteractiveBrowserCredential(
        cache_persistence_options=cpo,
        authentication_record=deserialized_record,
        )

    if not cred_json.get("babylon"):
        # serialize authentication_record to local file
        record = credential.authenticate()
        cred_json = record.serialize()

        # with open(fn, "wt") as outfile:
        #     outfile.write(cred_json)
        env.working_dir.set_encrypted_yaml_key(".secrets.yaml.encrypt", "babylon", cred_json
        )

    return credential


def pass_azure_credentials(func: Callable[..., Any]) -> Callable[..., Any]:
    """Grab Azure credentials and pass credentials"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        kwargs["azure_credentials"] = get_azure_credentials()
        return func(*args, **kwargs)

    return wrapper


def pass_azure_token(scope: str = "default") -> Callable[..., Any]:
    """Logs to Azure and pass token"""

    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            kwargs["azure_token"] = get_azure_token(scope)
            return func(*args, **kwargs)

        return wrapper

    return wrap_function
