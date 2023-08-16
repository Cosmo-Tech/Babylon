import json
import logging
import os
import shutil
import sys
import tempfile
import yaml
import pathlib

from hvac import Client
from typing import Optional
from typing import Union
from typing import Any
from flatten_json import unflatten_list
from ruamel.yaml import YAML

logger = logging.getLogger("Babylon")


def yaml_to_json(yaml_str: str) -> str:
    """
    Converts a yaml string to a json string
    """
    data = yaml.safe_load(yaml_str)
    return json.dumps(data, indent=4, default=str)


def read_yaml_key_from_context(yaml_file: pathlib.Path, context_id: str, key: str) -> str:
    """
    Will read a key from a yaml file and return the value
    :param yaml_file: path to the file to open
    :param context_id
    :param key: key to load
    :return: value of the key if found else None
    """
    try:
        _y = yaml.safe_load(yaml_file.open())
        _v = _y[context_id][key]
        return _v
    except (IOError, KeyError):
        return None


def read_yaml_key(yaml_file: pathlib.Path, key: str) -> Optional[object]:
    """
    Will read a key from a yaml file and return the value
    :param yaml_file: path to the file to open
    :param key: key to load
    :return: value of the key if found else None
    """
    try:
        _y = yaml.safe_load(yaml_file.open())
        _v = _y[key]
        return _v
    except (IOError, KeyError):
        return None


def set_nested_key(dic: dict[str, Any], keys: Union[list[str], str], value: Any) -> dict[str, Any]:
    """Sets a nested key in a dict

    :param dic: input dictionary
    :param keys: key or list of keys of nested
    :param value: value to set
    :return: new dictionary
    """
    dic = dic or {}
    if isinstance(keys, str):
        dic[keys] = value
        return dic
    else:
        nest = dic
        for key in keys[:-1]:
            nest = nest.setdefault(key, {})
        nest[keys[-1]] = value
    return dic


def write_yaml_value(yaml_file: pathlib.Path, keys: Union[list[str], str], value: str) -> None:
    """
    This function aloow to update a YAML file values
    :param yaml_file: path to the file to open
    :param keys: key to load
    :param value: the new value of the key
    :return : None
    """

    _commented_yaml_loader = YAML()
    try:
        with yaml_file.open(mode='r') as file:
            commented_file = _commented_yaml_loader.load(file) or {}
            commented_file = set_nested_key(commented_file, keys, value)
        with yaml_file.open(mode='w') as file:
            _commented_yaml_loader.dump(commented_file, yaml_file)
    except OSError:
        return


def write_yaml_value_from_context(yaml_file: pathlib.Path, context_id: str, keys: Union[list[str], str],
                                  value: str) -> None:
    """
    This function aloow to update a YAML file values
    :param yaml_file: path to the file to open
    :param context_id: context of project
    :param keys: key to load
    :param value: the new value of the key
    :return : None
    """
    _commented_yaml_loader = YAML()
    try:
        with yaml_file.open(mode='r') as file:
            commented_file = _commented_yaml_loader.load(file) or {}
            temp_file = commented_file[context_id]
            nested_dict = set_nested_key(temp_file, keys, value)
            commented_file[context_id] = nested_dict
        with yaml_file.open(mode='w') as file:
            _commented_yaml_loader.dump(commented_file, yaml_file)
    except OSError:
        return


def compare_yaml_keys(template_yaml: pathlib.Path, target_yaml: pathlib.Path) -> tuple[set, set]:
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
        _target = yaml.safe_load(_ta)
        try:
            for k, v in _template.items():
                try:
                    _target.setdefault(k, v)
                except AttributeError:
                    _target = dict()
                    _target.setdefault(k, v)
        except AttributeError:
            pass
    with target_yaml.open("w") as _ta:
        yaml.safe_dump(_target, _ta)


def get_file_config_from_keys(hvac_client: Client, context_id: str, config_file: pathlib.Path, key_name: str,
                              resource: str, tenant_id: str):
    organization_name = os.environ.get('BABYLON_ORG_NAME', '')
    response = hvac_client.read(path=f'{organization_name}/{tenant_id}/babylon/config/{resource}/{key_name}',)
    if not response:
        logger.info(f"{organization_name}/{tenant_id}:babylon/config/{resource}/{key_name} not found")
        sys.exit(1)
    data = unflatten_list(response['data'], separator=".")
    yaml_file = yaml.dump({context_id: data})
    tmpf = tempfile.NamedTemporaryFile(mode="w+")
    tmpf.write(yaml_file)
    tmpf.seek(0)
    shutil.copy(tmpf.name, config_file)
    tmpf.flush()
    tmpf.close()
