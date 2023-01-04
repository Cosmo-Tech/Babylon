import json
import pathlib
import re
import logging
from typing import Any
from typing import Iterable

import click
import yaml

from .environment import Environment

camel_pat = re.compile(r'([A-Z])')
logger = logging.getLogger("Babylon")


def camel_to_underscore(name: Any) -> Any:
    """
    Will convert a string from camelCase to snake_case
    will have no effect if the parameter is not a string
    :param name: the string to convert
    :return: the converted string
    """
    if isinstance(name, str):
        return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)
    return name


def underscore_to_camel(name: Any) -> Any:
    """
    Will convert a string from snake_case to camelCase
    will have no effect if the parameter is not a string
    :param name: the string to convert
    :return: the converted string
    """
    if isinstance(name, str):
        components = name.split('_')
        return components[0] + ''.join(c.title() for c in components[1:])
    return name


def convert_keys_case(element: Any, convert_function) -> Any:
    """
    Will apply a convert function to all keys in an object
    :param element: the object to be updated
    :param convert_function: the function to apply
    :return: an object of the same type as the original one where all dict keys had the convert_function applied
    """
    if isinstance(element, dict):
        new_element = dict()
        for k, v in element.items():
            if k in ["parametersValues", "parameters_values"]:
                new_element[convert_function(k)] = dict() if not v else v.copy()
            elif v:
                new_element[convert_function(k)] = convert_keys_case(v, convert_function)
        return new_element
    if isinstance(element, list):
        new_element = list()
        for e in element:
            new_element.append(convert_keys_case(e, convert_function))
        return new_element
    return element


def filter_api_response_item(api_response_body: Any, fields: Iterable[str]) -> Any:
    """
    This function allow to apply a filter on an api unique response body keys
    :param api_response_body: A single api response data in key=>value format
    :param fields: A Set of keys witch will be keep in the response
    :return None if api_response_body is empty or if the keys specified in fields parameter don't exist
        else the filtered response data
    """
    _api_response_body = api_response_body.to_dict()
    return {_key: _value for _key, _value in _api_response_body.items() if _key in fields}


def filter_api_response(api_response_body: Iterable, fields: Iterable[str]) -> Any:
    """
    This function allow to apply a filter on an api response list body keys
    :param api_response_body: A Set api response data in key=>value format
    :param fields: A Set of keys witch will be keep in the response
    :return None if api_response_body is empty or if the keys specified in fields parameter don't exist,
        else the filtered response data
    """
    return [filter_api_response_item(ele, fields) for ele in api_response_body]


def get_api_file(api_file_path: str, use_working_dir_file: bool):
    """
    This function will try to find the correct file, and return its content
        in a format ready to be used with the cosmotech api
    Accepts yaml and json files
    :param api_file_path: The path to the file to be loaded
    :param use_working_dir_file: Should the path be relative to the working directory ?
    :return: None if the file was not found, else the content of the loaded file
    """
    _file_path = pathlib.Path(api_file_path)
    if use_working_dir_file:
        _file_path = click.get_current_context().find_object(Environment).working_dir.get_file(api_file_path)
    if not _file_path.exists():
        logger.error(f"{_file_path} does not exists.")
        return None

    ext = _file_path.suffix

    with open(_file_path) as _file:
        if ext == ".json":
            logger.debug("Reading a json file")
            solution_content = json.load(_file)
        elif ext == ".yaml":
            logger.debug("Reading a yaml file")
            solution_content = yaml.safe_load(_file)
        else:
            logger.error(f"Unknown file format for {_file_path}, only accepted format are json and yaml")
            return None

    # Ensure correct case for the python API (python api use snake_case, while other versions use camelCase)
    converted_solution_content = convert_keys_case(solution_content, camel_to_underscore)
    return converted_solution_content
