import os
import pathlib

import click

from .configuration import Configuration
from .working_dir import WorkingDir


class Environment:

    def __init__(self, configuration: Configuration, working_dir: WorkingDir):
        self.dry_run = False
        self.configuration = configuration
        self.working_dir = working_dir


def initialize_environment() -> Environment:
    config_directory = pathlib.Path(os.environ.get('BABYLON_CONFIG_DIRECTORY', click.get_app_dir("babylon")))
    conf = Configuration(config_directory=config_directory)

    working_directory_path = pathlib.Path(os.environ.get('BABYLON_WORKING_DIRECTORY', "."))
    work_dir = WorkingDir(working_dir_path=working_directory_path)

    env = Environment(configuration=conf, working_dir=work_dir)
    return env
