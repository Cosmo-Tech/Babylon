import logging
from typing import Optional

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential

from ...utils.decorators import require_platform_key
from ...utils.decorators import requires_external_program

logger = logging.getLogger("Babylon")


@requires_external_program("az")
@require_platform_key("api_scope", "api_scope")
def azure_connect(api_scope: Optional[str] = None):
    """Group allowing communication with Microsoft Azure Cloud"""
    creds = DefaultAzureCredential()
    try:
        # Authentication fails only when token can't be retrieved
        creds.get_token(api_scope)
        return creds
    except ClientAuthenticationError as _e:
        logger.error("Please login to azure CLI with `az login`")
        raise _e
