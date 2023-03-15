import json
import logging
import os
import pathlib
import re
from collections import defaultdict
from typing import Any
from typing import List
from typing import Optional

import click
import jmespath

from .configuration import Configuration
from .working_dir import WorkingDir

logger = logging.getLogger("Babylon")

WORKING_DIR_STRING = "workdir"
DEPLOY_STRING = "deploy"
PLATFORM_STRING = "platform"
STORE_STRING = "datastore"
SECRETS_STRING = "secrets"
PATH_SYMBOL = "%"


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Environment(metaclass=SingletonMeta):

    def __init__(self):
        self.dry_run = False
        workingdir_path = pathlib.Path(os.environ.get('BABYLON_WORKING_DIRECTORY', "."))
        self.working_dir = WorkingDir(workingdir_path)
        config_path = pathlib.Path(os.environ.get('BABYLON_CONFIG_DIRECTORY', click.get_app_dir("babylon")))
        self.configuration = Configuration(config_path)
        self.data_store: defaultdict[str, Any] = defaultdict()
        self.reset_data_store()

    def set_configuration(self, configuration_path: pathlib.Path):
        self.configuration = Configuration(config_directory=configuration_path)

    def set_working_dir(self, working_dir_path: pathlib.Path):
        self.working_dir = WorkingDir(working_dir_path=working_dir_path)

    def reset_data_store(self):

        def _nested_dict():
            return defaultdict(_nested_dict)

        self.data_store = _nested_dict()

    def store_data(self, data_path: List[str], value: Any) -> bool:
        """
        Will use a data path composed of multiple keys to insert data in the store
        :param data_path: succession of keys to be the target to store the data
        :param value: the element to be stored
        :return: Was the element successfully stored ?
        """
        if not len(data_path):
            raise KeyError("Require at least one component for the data path")

        current_store = self.data_store

        *intermediate_keys, final_key = data_path

        for key in intermediate_keys:
            current_store = current_store[key]
            if not isinstance(current_store, dict):
                raise KeyError("Data path is incorrect")

        current_store[final_key] = value

        return True

    def get_data(self, data_path: List[str]) -> Any:
        """
        Will look up a data from a given data path and return it
        :param data_path: the path to the data to get
        :return: the value of the data or None if it is not existent
        """
        if not len(data_path):
            raise KeyError("Require at least one component for the data path")

        r = self.convert_data_query(f"{PATH_SYMBOL}{STORE_STRING}{PATH_SYMBOL}" + ".".join(data_path))
        if r is None:
            raise KeyError("Data path can't get data")
        return r

    def printable_store(self) -> str:
        return json.dumps(self.data_store, indent=2, default=str)

    def convert_data_query(self, query: str) -> Any:

        extracted_content = self.extract_value_content(query)
        if not extracted_content:
            logger.debug(f"  '{query}' -> no conversion applied")
            return None

        _type, _file, _query = extracted_content
        # Check content of platform / deploy / secrets
        possibles = {
            DEPLOY_STRING: (self.configuration.get_deploy(), self.configuration.get_deploy_path()),
            PLATFORM_STRING: (self.configuration.get_platform(), self.configuration.get_platform_path())
        }

        if _type in possibles:
            logger.debug(f"    Detected parameter type '{_type}' with query '{_query}'")
            _data, _path = possibles.get(_type)
            r = jmespath.search(_query, _data)
            if r is None:
                raise KeyError(f"Could not find results for query '{_query}' in {_path}")
        elif _type == SECRETS_STRING:
            data = self.working_dir.get_file_content(".secrets.yaml.encrypt")
            r = jmespath.search(_query, data)
        elif _type == STORE_STRING:
            logger.debug(f"    Detected parameter type '{_type}' with query '{_query}'")
            r = jmespath.search(_query, self.data_store)
        else:
            # Check content of workdir
            logger.debug(f"    Detected parameter type '{_type}' with query '{_query}' on file '{_file}'")
            wd = self.working_dir
            if not wd.requires_file(_file):
                raise KeyError(f"File '{_file}' does not exists in current working dir.")

            _content = wd.get_file_content(_file)
            r = jmespath.search(_query, _content)
            if r is None:
                raise KeyError(f"Could not find results for query '{_query}' in '{wd.get_file(_file)}'")

        return r

    @staticmethod
    def auto_completion_guide():
        bases = [WORKING_DIR_STRING + '[]', SECRETS_STRING, DEPLOY_STRING, PLATFORM_STRING, STORE_STRING]
        base_names = [f"{PATH_SYMBOL}{base}{PATH_SYMBOL}" for base in bases]
        return base_names

    @staticmethod
    def extract_value_content(value: Any) -> Optional[tuple[str, Optional[str], str]]:
        """
        Extract interesting information from a given value
        :param value: Value of the parameter to extract
        :return: None if value has no interesting info else element, filepath, and query
        """

        if not isinstance(value, str):
            return None

        check_regex = re.compile(f"{PATH_SYMBOL}"
                                 f"({SECRETS_STRING}|{PLATFORM_STRING}|{DEPLOY_STRING}|"
                                 f"{WORKING_DIR_STRING}|{STORE_STRING})"
                                 f"(?:(?<={WORKING_DIR_STRING})\\[(.+)])?"
                                 f"{PATH_SYMBOL}"
                                 f"(.+)")

        # Regex groups captures :
        # 1 : Element to query : platform/deploy/workdir
        # 2 : File path to query in case of a working dir
        # 3 : jmespath query to apply

        match_content = check_regex.match(value)
        if not match_content:
            return None
        _type, _file, _query = match_content.groups()

        return _type, _file, _query

    def fill_template(self,
                      template_file: pathlib.Path,
                      data: dict[str, Any] = {},
                      use_working_dir_file: bool = False) -> str:
        """
        Fills a template with environment data using queries
        :param template_file: Input template file path
        :type template_file: str
        :return: filled template
        """
        REMOVE_MARKER = "\\REMOVE_LINE\\"

        def lookup_value(match: re.Match[str]) -> str:
            key = str(match.group(1))
            value = data.get(key) or self.convert_data_query(key)
            if not value:
                logger.warning(f"Missing key {key} in template data, removing line...")
                return REMOVE_MARKER
            return value

        if use_working_dir_file:
            template_file = self.working_dir.get_file(str(template_file))
        with open(template_file, "r") as _file:
            template_content = _file.read()
        filled = re.sub(r"\$\{(.+)\}", lookup_value, template_content)
        filtered = "\n".join([line for line in filled.split("\n") if REMOVE_MARKER not in line])
        # Removing last commas for json files
        return re.sub(r'''(?<=[}\]"']),(?!\s*[{["'])''', "", filtered)
