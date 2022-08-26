import os
import pathlib
import pprint
import shutil
import subprocess
import sys
from functools import wraps
from logging import Logger
from typing import Optional

import click
import yaml

from . import TEMPLATE_FOLDER_PATH
from .yaml_utils import read_yaml_key


class Configuration:
    """
    Base object created to store in file the configuration used in babylon
    """

    def __save_after_run(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            r = func(self, *args, **kwargs)
            self.save_config()
            return r

        return wrapper

    def __init__(self,
                 logger: Logger,
                 config_directory: pathlib.Path = pathlib.Path(click.get_app_dir("babylon"))):
        self.config_dir = config_directory
        self.logger = logger
        if not self.config_dir.exists():
            self.logger.warning("No config folder existing - Creating it.")
            shutil.copytree(TEMPLATE_FOLDER_PATH / "ConfigTemplate", self.config_dir)
            self.deploy = self.config_dir.absolute() / pathlib.Path(str(read_yaml_key(self.config_dir / "config.yaml",
                                                                                      "deploy")))
            self.platform = self.config_dir.absolute() / pathlib.Path(str(read_yaml_key(self.config_dir / "config.yaml",
                                                                                        "platform")))
            self.save_config()

        self.deploy = pathlib.Path(str(read_yaml_key(self.config_dir / "config.yaml", "deploy")))
        self.platform = pathlib.Path(str(read_yaml_key(self.config_dir / "config.yaml", "platform")))
        self.plugins = read_yaml_key(self.config_dir / "config.yaml", "plugins") or list()

    def get_active_plugins(self) -> list[(str, pathlib.Path)]:
        """
        Yields all activated plugins path
        """
        for _p in self.plugins:
            if _p['active']:
                yield _p['name'], pathlib.Path(_p['path'])

    def get_available_plugin(self) -> list[str]:
        """
        Yields all available plugin names
        """
        for _p in self.plugins:
            yield _p['name']

    @__save_after_run
    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Will activate a given plugin
        :param plugin_name: the plugin to activate
        :return: Did the plugin get activated ?
        """
        for _p in self.plugins:
            if _p['name'] == plugin_name:
                _p['active'] = True
                return True
        return False

    @__save_after_run
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Will deactivate a given plugin
        :param plugin_name: the plugin to deactivate
        :return: Did the plugin get deactivated ?
        """
        for _p in self.plugins:
            if _p['name'] == plugin_name:
                _p['active'] = False
                return True
        return False

    @__save_after_run
    def remove_plugin(self, plugin_name: str) -> bool:
        """
        Will remove a given plugin
        :param plugin_name: the plugin to remove
        :return: Did the plugin get removed ?
        """
        _plugins = list()
        for _p in self.plugins:
            if _p['name'] != plugin_name:
                _plugins.append(_p)
        self.plugins = _plugins
        return True

    @__save_after_run
    def add_plugin(self, plugin_path: pathlib.Path) -> Optional[str]:
        """
        Will add a plugin to the config given a plugin path
        :param plugin_path: path to the plugin folder to add
        :return: The name of the plugin added, or None if plugin could not be added
        """
        plugin_config_path = plugin_path / "plugin_config.yaml"
        if not plugin_config_path.exists():
            self.logger.error(f"`{plugin_path}` is not a valid plugin folder")
            return None
        plugin_name = read_yaml_key(plugin_config_path, "plugin_name")
        if plugin_name is None:
            self.logger.error(f"`{plugin_path}` is not a valid plugin folder, no plugin_name found.")
            return None

        if plugin_name in self.get_available_plugin():
            self.logger.error(f"`{plugin_name}` is an already existing plugin")
            return None

        requirements_path = plugin_path / "requirements.txt"
        if requirements_path.exists():
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path.absolute())])
            except subprocess.CalledProcessError:
                self.logger.error(f"Issues while installing requirements for `{plugin_name}`")
                return None

        plugin_entry = dict(name=plugin_name, path=str(plugin_path.absolute()), active=True)
        self.plugins.append(plugin_entry)
        return str(plugin_name)

    def __list_config_folder_files(self, folder_name: str) -> list[str]:
        for root, _, files in os.walk(self.config_dir / folder_name):
            for _f in files:
                _file_name = pathlib.Path(root) / pathlib.Path(_f)
                yield _file_name.absolute()

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
    def set_deploy(self, deploy_path: pathlib.Path) -> bool:
        """
        Change configured deployment to the one given
        :param deploy_path: the deployment path
        :return: True if the change was a success
        """
        if deploy_path.exists():
            self.deploy = deploy_path.absolute()
            return True
        else:
            self.logger.error(f"{deploy_path} is not an existing deployment")
            return False

    @__save_after_run
    def set_platform(self, platform_path: pathlib.Path) -> bool:
        """
        Change configured platform to the one given
        :param platform_path: the platform path
        :return: True if the change was a success
        """
        if platform_path.exists():
            self.platform = platform_path.absolute()
            return True
        else:
            self.logger.error(f"{platform_path} is not an existing platform")
            return False

    def create_deploy(self, deploy_name: str):
        """
        Create a new deployment file from the template and open it with the default text editor
        :param deploy_name: the name of the new deploy
        """
        _target = self.config_dir / "deployments" / f"{deploy_name}.yaml"
        if _target.exists():
            self.logger.error(f"Deployment {deploy_name} already exists")
            return
        _t = shutil.copy(TEMPLATE_FOLDER_PATH / "ConfigTemplate/deployments/deploy.yaml", _target)
        click.edit(filename=str(_t))

    def create_platform(self, platform_name: str):
        """
        Create a new platform file from the template and open it with the default text editor
        :param platform_name: the name of the new platform
        """
        _target = self.config_dir / "platforms" / f"{platform_name}.yaml"
        if _target.exists():
            self.logger.error(f"Platform {platform_name} already exists")
            return
        _t = shutil.copy(TEMPLATE_FOLDER_PATH / "ConfigTemplate/platforms/platform.yaml", _target)
        click.edit(filename=str(_t))

    def edit_deploy(self, deploy_name: str):
        """
        Open a given deployment file with the default text editor
        :param deploy_name: the name of the deployment
        """
        deploy_path = self.config_dir / "deployments" / f"{deploy_name}.yaml"
        if not deploy_path.exists():
            self.logger.error(f"Deployment {deploy_name} does not exists")
        else:
            click.edit(filename=str(deploy_path))

    def edit_platform(self, platform_name: str):
        """
        Open a given platform file with the default text editor
        :param platform_name: the name of the platform
        """
        platform_path = self.config_dir / "platforms" / f"{platform_name}.yaml"
        if not platform_path.exists():
            self.logger.error(f"Platform {platform_name} does not exists")
        else:
            click.edit(filename=str(platform_path))

    def save_config(self):
        """
        Save the current config
        """
        _d = yaml.safe_load(open(self.config_dir / "config.yaml", "r"))
        _d['deploy'] = str(self.deploy)
        _d['platform'] = str(self.platform)
        _d['plugins'] = self.plugins

        self.logger.debug(f"Saving config:\n{pprint.pformat(_d)}")

        yaml.safe_dump(_d, open(self.config_dir / "config.yaml", "w"))

    def get_deploy_path(self) -> Optional[pathlib.Path]:
        """
        Get path to the current deployment file
        :return: path to the current deployment file
        """
        if self.deploy:
            return self.deploy
        return None

    def get_platform_path(self) -> Optional[pathlib.Path]:
        """
        Get path to the current platform file
        :return: path to the current platform file
        """
        if self.platform:
            return self.platform
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
        _ret.append(f"  deployment: {self.get_deploy_path()}")
        for k, v in yaml.safe_load(open(self.get_deploy_path())).items():
            _ret.append(f"    {k}: {v}")
        _ret.append(f"  platform: {self.get_platform_path()}")
        for k, v in yaml.safe_load(open(self.get_platform_path())).items():
            _ret.append(f"    {k}: {v}")
        _ret.append(f"  plugins:")
        for plugin in self.plugins:
            state = '[' + ("x" if plugin['active'] else " ") + "]"
            _ret.append(f"    {state} {plugin['name']}: {plugin['path']}")
        return "\n".join(_ret)
