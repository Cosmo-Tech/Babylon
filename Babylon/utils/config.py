import os
import pathlib
import pprint
import shutil
from functools import wraps
from logging import Logger
from typing import Optional

import click
import yaml

from . import TEMPLATE_FOLDER_PATH
from .yaml_utils import read_yaml_key


class Config:

    def __save_after_run(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.save_config()

        return wrapper

    def __init__(self, logger: Logger):
        self.config_dir = pathlib.Path(click.get_app_dir("babylon"))
        self.logger = logger
        if not self.config_dir.exists():
            self.logger.warning("No config folder existing - Creating it.")
            shutil.copytree(TEMPLATE_FOLDER_PATH / "ConfigTemplate", self.config_dir)

        self.deploy = str(read_yaml_key(self.config_dir / "config.yaml", "deploy"))
        self.platform = str(read_yaml_key(self.config_dir / "config.yaml", "platform"))

    def __list_config_folder_files(self, folder_name: str) -> list[str]:
        for _, _, files in os.walk(self.config_dir / folder_name):
            for _f in files:
                yield _f

    def list_deploys(self) -> list[str]:
        """
        List existing deployment configurations
        :return: a list of available deployments names
        """
        return self.__list_config_folder_files("deployments")

    def list_platforms(self) -> list[str]:
        """
        List existing platform configurations
        :return: a list of available platforms names
        """
        return self.__list_config_folder_files("platforms")

    @__save_after_run
    def set_deploy(self, deploy_name: str) -> bool:
        """
        Change configured deployment to the one given
        :param deploy_name: the deployment name
        :return: True if the change was a success
        """
        deploy_path = self.config_dir / "deployments" / f"{deploy_name}.yaml"
        if deploy_path.exists():
            self.deploy = deploy_name
            return True
        else:
            self.logger.error(f"{deploy_name} is not an existing deploy")
            return False

    @__save_after_run
    def set_platform(self, platform_name: str):
        """
        Change configured platform to the one given
        :param platform_name: the platform name
        :return: True if the change was a success
        """
        if platform_name in self.list_deploys():
            self.platform = platform_name
            return True
        else:
            self.logger.error(f"{platform_name} is not an existing platform")
            return False

    def create_deploy(self, deploy_name: str):
        """
        Create a new deployment file from the template and open it with the default text editor
        :param deploy_name: the name of the new deploy
        """
        _t = shutil.copy(TEMPLATE_FOLDER_PATH / "ConfigTemplate/deployments/deploy.yaml",
                         self.config_dir / "deployments" / f"{deploy_name}.yaml")
        click.edit(filename=str(_t))

    def create_platform(self, platform_name: str):
        """
        Create a new platform file from the template and open it with the default text editor
        :param platform_name: the name of the new platform
        """
        _t = shutil.copy(TEMPLATE_FOLDER_PATH / "ConfigTemplate/platforms/platform.yaml",
                         self.config_dir / "platforms" / f"{platform_name}.yaml")
        click.edit(filename=str(_t))

    def edit_deploy(self, deploy_name: str):
        """
        Open a given deployment file with the default text editor
        :param deploy_name: the name of the deployment
        """
        deploy_path = self.config_dir / "deployments" / f"{deploy_name}.yaml"
        if not deploy_path.exists():
            self.logger.error(f"{deploy_name} does not exists")
        else:
            click.edit(filename=str(deploy_path))

    def edit_platform(self, platform_name: str):
        """
        Open a given platform file with the default text editor
        :param platform_name: the name of the platform
        """
        platform_path = self.config_dir / "platforms" / f"{platform_name}.yaml"
        if not platform_path.exists():
            self.logger.error(f"{platform_name} does not exists")
        else:
            click.edit(filename=str(platform_path))

    def save_config(self):
        """
        Save the current config
        """
        _d = dict(deploy=self.deploy, platform=self.platform)
        yaml.safe_dump(_d, (self.config_dir / "config.yaml").open())
        self.logger.debug(f"Saving config:\n{pprint.pformat(_d)}")

    def get_deploy_path(self) -> Optional[pathlib.Path]:
        """
        Get path to the current deployment file
        :return: path to the current deployment file
        """
        if self.deploy:
            return self.config_dir / "deployments" / (self.deploy + ".yaml")
        return None

    def get_platform_path(self) -> Optional[pathlib.Path]:
        """
        Get path to the current platform file
        :return: path to the current platform file
        """
        if self.platform:
            return self.config_dir / "platforms" / (self.platform + ".yaml")
        return None

    def get_deploy_var(self, var_name) -> Optional[object]:
        """
        Read a key value from the current deployment file
        :param var_name: the key to read
        :return: the value of the key in the deployment file if exists else None
        """
        if not (_path := self.get_deploy_path()).exists():
            return None
        else:
            return read_yaml_key(_path, var_name)

    def get_platform_var(self, var_name) -> Optional[object]:
        """
        Read a key value from the current platform file
        :param var_name: the key to read
        :return: the value of the key in the platform file if exists else None
        """
        if not (_path := self.get_platform_path()).exists():
            return None
        else:
            return read_yaml_key(_path, var_name)

    def check_api(self) -> bool:
        """
        :return: True if the api targeted in the deploy is the same as the platform we use
        """
        config_platform = self.get_platform_var("api_url")
        target_platform = self.get_deploy_var("api_url")

        if config_platform != target_platform:
            self.logger.warning("The platform targeted by the deploy is not the platform configured.")
            self.logger.warning(f"  deploy  : {target_platform}")
            self.logger.warning(f"  platform: {config_platform}")
            return False
        return True

    def __str__(self):
        _ret = list()
        _ret.append("Configuration:")
        _ret.append(f"  dir: {self.config_dir}")
        _ret.append(f"  deployment: {self.deploy}")
        for k, v in yaml.safe_load(open(self.get_deploy_path())).items():
            _ret.append(f"    {k}: {v}")
        _ret.append(f"  platform: {self.platform}")
        for k, v in yaml.safe_load(open(self.get_platform_path())).items():
            _ret.append(f"    {k}: {v}")
        return "\n".join(_ret)
