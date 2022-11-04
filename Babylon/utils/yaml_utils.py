import pathlib
from typing import Any, Optional, Tuple

import yaml
from ruamel.yaml import YAML  # Allow to load and dump Yaml file with comment


def read_yaml_key(yaml_file: pathlib.Path, key: str) -> Optional[Any]:
    """
    Will read a key from a yaml file and return the value
    :param yaml_file: path to the file to open
    :param key: key to load
    :return: value of the key if found else None
    """
    if not yaml_file.is_file():
        return None
    with yaml_file.open("r") as file:
        _y = yaml.safe_load(file)
    return _y.get(key)


def write_yaml_value(yaml_file: pathlib.Path, key: str, value: str) -> None:
    """
    This function aloow to update a YAML file values
    :param yaml_file: path to the file to open
    :param key: key to load
    :param value:the new value of the key
    :return : None
    """
    _commented_yaml_loader = YAML()
    with yaml_file.open(mode='rw') as file:
        _y = _commented_yaml_loader.load(file)
        _y[key] = value
        _commented_yaml_loader.dump(_y, yaml_file)


def compare_yaml_keys(template_yaml: pathlib.Path, target_yaml: pathlib.Path) -> Tuple[set, set]:
    """
    Compare two yaml files and return the different keys they contain
    :param template_yaml: Yaml file considered as the main file
    :param target_yaml: Yaml file to be compared to the template
    :return: 2 sets of keys :</br>
    - missing_keys : the keys from the template missing from the target</br>
    - superfluous_keys: the keys from the target that are not in the template
    """
    with template_yaml.open() as _te, target_yaml.open() as _ta:
        _template = yaml.safe_load(_te)
        _target = yaml.safe_load(_ta)
        try:
            _template_keys = set(_template.keys())
        except AttributeError:
            _template_keys = set()
        try:
            _target_keys = set(_target.keys())
        except AttributeError:
            _target_keys = set()
        missing_keys = _template_keys - _target_keys
        superfluous_keys = _target_keys - _template_keys
        return missing_keys, superfluous_keys


def complete_yaml(template_yaml: pathlib.Path, target_yaml: pathlib.Path):
    """
    Will add missing element from template in target
    :param template_yaml: Yaml file considered as the main file
    :param target_yaml: Yaml file to be compared to the template
    :return: Nothing
    """
    with template_yaml.open() as _te, target_yaml.open() as _ta:
        _template = yaml.safe_load(_te)
        _target = yaml.safe_load(_ta) or {}
        for k, v in _template.items():
            _target.setdefault(k, v)
    with target_yaml.open("w") as _ta:
        yaml.safe_dump(_target, _ta)
