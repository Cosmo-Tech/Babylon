import logging
from typing import Any
from typing import Optional

import requests

logger = logging.getLogger("Babylon")


def oauth_request(url: str,
                  access_token: str,
                  data: Any = {},
                  json_data: Any = "",
                  params: Any = {},
                  type: str = "GET") -> Optional[Any]:
    """Requests an API using OAuth authentication

    :param url: request url
    :type url: str
    :param type: request type [POST, PATCH, PUT, GET]
    :type type: str
    """
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
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
        response = request_func(url=url, headers=header, data=data, json=json_data, params=params)
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None
    if 200 < response.status_code >= 300:
        logger.error(f"Request failed ({response.status_code}): {response.text}")
        return None
    logger.debug(f"Request success ({response.status_code}): {response.text}")
    return response
