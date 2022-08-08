import os
import pathlib
import pprint
import shutil
from functools import wraps
from logging import Logger

import click
import yaml

from . import TEMPLATE_FOLDER_PATH


class Config:

    def __save_after_run(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.save_config()

        return wrapper

    @staticmethod
    def __read_yaml_key(_file, _key):
        try:
            _y = yaml.safe_load(_file.open())
            _v = _y[_key]
            return _v
        except:
            return None

    def __init__(self, logger: Logger):
        self.config_dir = pathlib.Path(click.get_app_dir("babylon"))
        self.logger = logger
        if not self.config_dir.exists():
            self.logger.warning("No config folder existing - Creating it.")
            shutil.copytree(TEMPLATE_FOLDER_PATH / "ConfigTemplate", self.config_dir)

        self.deploy = self.__read_yaml_key(self.config_dir / "config.yaml", "deploy")
        self.platform = self.__read_yaml_key(self.config_dir / "config.yaml", "platform")

    def __list_config_folder_files(self, folder_name: str) -> list[str]:
        for _, _, files in os.walk(self.config_dir / folder_name):
            for _f in files:
                yield _f

    def list_deploys(self) -> list[str]:
        return self.__list_config_folder_files("deployments")

    def list_platforms(self) -> list[str]:
        return self.__list_config_folder_files("platforms")

    @__save_after_run
    def set_deploy(self, deploy_name: str):
        deploy_path = self.config_dir / "deployments" / f"{deploy_name}.yaml"
        if deploy_path.exists():
            self.deploy = deploy_name
        else:
            self.logger.error(f"{deploy_name} is not an existing deploy")

    @__save_after_run
    def set_platform(self, platform_name: str):
        if platform_name in self.list_deploys():
            self.deploy = platform_name
        else:
            self.logger.error(f"{platform_name} is not an existing platform")

    def edit_file(self, file_path):
        self.logger.debug(f"Opening {file_path}")
        click.edit(filename=str(file_path))

    def create_deploy(self, deploy_name: str):
        _t = shutil.copy(TEMPLATE_FOLDER_PATH / "ConfigTemplate/deployments/deploy.yaml",
                         self.config_dir / "deployments" / f"{deploy_name}.yaml")
        self.edit_file(_t)

    def create_platform(self, platform_name: str):
        _t = shutil.copy(TEMPLATE_FOLDER_PATH / "ConfigTemplate/platforms/platform.yaml",
                         self.config_dir / "platforms" / f"{platform_name}.yaml")
        self.edit_file(_t)

    def edit_deploy(self, deploy_name: str):
        deploy_path = self.config_dir / "deployments" / f"{deploy_name}.yaml"
        if not deploy_path.exists():
            self.logger.error(f"{deploy_name} does not exists")
        else:
            self.edit_file(deploy_path)

    def edit_platform(self, platform_name: str):
        platform_path = self.config_dir / "platforms" / f"{platform_name}.yaml"
        if not platform_path.exists():
            self.logger.error(f"{platform_name} does not exists")
        else:
            self.edit_file(platform_path)

    def save_config(self):
        _d = dict(deploy=self.deploy, platform=self.platform)
        yaml.safe_dump(_d, (self.config_dir / "config.yaml").open())
        self.logger.debug(f"Saving config:\n{pprint.pformat(_d)}")

    def get_deploy_path(self):
        if self.deploy:
            return self.config_dir / "deployments" / self.deploy
        return None

    def get_platform_path(self):
        if self.platform:
            return self.config_dir / "platforms" / self.platform
        return None
