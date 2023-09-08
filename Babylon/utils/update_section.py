import logging
import pathlib

from typing import Any
from ruamel.yaml import YAML
from flatten_json import flatten, unflatten_list
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()
sep = "."


def get_section_and_replace(section: str, new_value: Any, data: dict, unflatten: bool = True):
    """Replace section in yaml file"""
    flatten_data = flatten(data, separator=sep)
    # add new section in flatten object
    if isinstance(new_value, list):
        # subclasses in new_value
        for index, key_new_section in enumerate(new_value):
            if isinstance(key_new_section, dict):
                # delete old section
                if section in flatten_data:
                    del flatten_data[section]
                # replace section
                flatten_tmp = flatten(key_new_section, separator=sep)
                for new_section_to_replace, key_new_section in flatten_tmp.items():
                    new_key = f"{section}.{new_section_to_replace}"
                    flatten_data.update({new_key: key_new_section})
            else:
                flatten_data.update({f"{section}.{index}": key_new_section})
    elif isinstance(new_value, dict):
        # flatten subclass dict in new_value
        flatten_tmp = flatten(new_value, separator=sep)
        # delete old section
        if section in flatten_data:
            del flatten_data[section]
        # replace section
        for new_section_to_replace, key_new_section in flatten_tmp.items():
            flatten_data.update({f"{section}.{new_section_to_replace}": key_new_section})
    else:
        flatten_data[section] = new_value

    if unflatten:
        final = unflatten_list(flatten_data, separator=sep)
    else:
        final = flatten_data
    return final


def update_section_yaml(origin_file: pathlib.Path, target_file: pathlib.Path, section: str, new_value: Any):
    yaml_loader = YAML()
    with origin_file.open(mode='r') as _f:
        data = yaml_loader.load(_f)

    result = get_section_and_replace(section, new_value, data)

    with target_file.open(mode='w') as _f:
        yaml_loader.dump(result, target_file)
