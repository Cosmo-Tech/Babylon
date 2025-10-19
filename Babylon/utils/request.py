import logging
import requests

from typing import Any
from typing import Optional
from time import sleep

logger = logging.getLogger("Babylon")


def poll_request(retries: int = 5, check_for_failure: bool = False, **kwargs: dict[str, Any]):
    """Do a request until success or failure with a long polling"""
    for _ in range(0, retries):
        response = oauth_request(**kwargs)
        if check_for_failure and response is None:
            return
        if response and response.status_code <= 300:
            logger.info("Request polling succeeded")
            return response
        sleep(1)
    raise ValueError("Request polling failed")


def oauth_request(url: str,
                  access_token: str,
                  type: str = "GET",
                  content_type: str = "application/json",
                  **kwargs: Any) -> Optional[Any]:
    """Requests an API using OAuth authentication

    :param content_type:
    :param url: request url
    :type url: str
    :param type: request type [POST, PATCH, PUT, GET]
    :type type: str
    """
    headers = {'Authorization': f'Bearer {access_token}', "Content-Type": content_type, **kwargs.pop("headers", {})}
    request_funcs = {
        "POST": requests.post,
        "PATCH": requests.patch,
        "PUT": requests.put,
        "GET": requests.get,
        "DELETE": requests.delete,
    }
    request_func = request_funcs.get(type.upper())
    if not request_func:
        logger.warning(f"Could not find request of type {type}")
        return None
    try:
        response = request_func(url=url, headers=headers, **kwargs)
    except Exception as e:
        logger.warning(f"Request failed: {e}")
        return None
    if response.status_code == 401:
        logger.error("[api] Unauthorized (401): token missing or expired. Refresh token or check client credentials.")
        return None
    if response.status_code == 403:
        logger.error(
            "[api] Forbidden (403): token valid but lacks required roles/scopes. Check Keycloak client permissions.")
        return None
    if not response.ok:
        logger.warning(f"[api] Request failed ({response.status_code}): {response.text}")
        return None
    if response.status_code >= 300:
        logger.warning(f"[api] Failed: ({response.status_code}): {response.text}")
        return None
    logger.debug(f"[api] Request success ({response.status_code}): {response.text}")
    return response
