import os
import pathlib
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

    def __init__(self):
        self.dry_run = False

        self.set_configuration(pathlib.Path(os.environ.get('BABYLON_CONFIG_DIRECTORY', click.get_app_dir("babylon"))))
        self.set_working_dir(pathlib.Path(os.environ.get('BABYLON_WORKING_DIRECTORY', ".")))

    def set_configuration(self, configuration_path: pathlib.Path):
        self.configuration = Configuration(config_directory=configuration_path)

    def set_working_dir(self, working_dir_path: pathlib.Path):
        self.working_dir = WorkingDir(working_dir_path=working_dir_path)
