import logging
from typing import Any
from typing import Optional
from time import sleep

import requests

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


def oauth_request(url: str, access_token: str, type: str = "GET", **kwargs: Any) -> Optional[Any]:
    """Requests an API using OAuth authentication

    :param url: request url
    :type url: str
    :param type: request type [POST, PATCH, PUT, GET]
    :type type: str
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        "Content-Type": "application/json",
        **kwargs.pop("headers", {})
    }
    request_funcs = {
        "POST": requests.post,
        "PATCH": requests.patch,
        "PUT": requests.put,
        "GET": requests.get,
        "DELETE": requests.delete,
    }
    request_func = request_funcs.get(type.upper())
    if not request_func:
        logger.error(f"Could not find request of type {type}")
        return None
    try:
        response = request_func(url=url, headers=headers, **kwargs)
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None
    if response.status_code >= 300:
        logger.error(f"Request failed ({response.status_code}): {response.text}")
        return None
    logger.debug(f"Request success ({response.status_code}): {response.text}")
    return response
