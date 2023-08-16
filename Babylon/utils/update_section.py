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
    s = flatten(data, separator=sep)
    if isinstance(new_value, list):
        for i, k in enumerate(new_value):
            if isinstance(k, dict):
                if section in s:
                    del s[section]
                tmp = flatten(k, separator=sep)
                for w, k in tmp.items():
                    s.update({f"{section}.{i}.{w}": k})
            else:
                s.update({f"{section}.{i}": k})
    elif isinstance(new_value, dict):
        tmp = flatten(new_value, separator=sep)
        if section in s:
            del s[section]
        for i, k in tmp.items():
            s.update({f"{section}.{i}": k})
    else:
        s[section] = new_value

    if unflatten:
        final = unflatten_list(s, separator=sep)
    else:
        final = s
    return final


def update_section_yaml(origin_file: pathlib.Path, target_file: pathlib.Path, section: str, new_value: Any):
    yaml_loader = YAML()
    with origin_file.open(mode='r') as _f:
        data = yaml_loader.load(_f)

    result = get_section_and_replace(section, new_value, data)

    with target_file.open(mode='w') as _f:
        yaml_loader.dump(result, target_file)
