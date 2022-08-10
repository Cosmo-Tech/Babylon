import json
import pathlib
import re

from typing import Any

import yaml

camel_pat = re.compile(r'([A-Z])')


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
            if v is not None:
                new_element[convert_function(k)] = convert_keys_case(v, convert_function)
        return new_element
    if isinstance(element, list):
        new_element = list()
        for e in element:
            new_element.append(convert_keys_case(e, convert_function))
        return new_element
    return element


def get_api_file(api_file_path: str, use_solution_file: bool, solution, logger):
    """
    This function will try to find the correct file, and return its content in a format ready to be used with the cosmotech api
    Accepts yaml and json files
    :param api_file_path: The path to the file to be loaded
    :param use_solution_file: Should the path be relative to the solution ?
    :param solution: The current solution item
    :param logger: the logger to be used to log info
    :return: None if the file was not found, else the content of the loaded file
    """
    _file_path = pathlib.Path(api_file_path)
    if use_solution_file:
        _file_path = solution.get_file(api_file_path)
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
