import json
import os
import pathlib
from collections import defaultdict
from typing import Any
from typing import List
from typing import Optional

import click

from .configuration import Configuration
from .working_dir import WorkingDir


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
    configuration: Optional[Configuration] = None
    working_dir: Optional[WorkingDir] = None

    data_store = None

    def __init__(self):
        self.dry_run = False

        self.set_configuration(pathlib.Path(os.environ.get('BABYLON_CONFIG_DIRECTORY', click.get_app_dir("babylon"))))
        self.set_working_dir(pathlib.Path(os.environ.get('BABYLON_WORKING_DIRECTORY', ".")))
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
        current_store = self.data_store

        *intermediate_keys, final_key = data_path

        for key in intermediate_keys:
            current_store = current_store.get(key)
            if not isinstance(current_store, dict):
                raise KeyError("Data path is incorrect")

        return current_store.get(final_key)

    def printable_store(self) -> str:
        return json.dumps(self.data_store, indent=2, default=str)
