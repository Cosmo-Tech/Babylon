import logging
import os
import pathlib
import pprint
import shutil
import subprocess
import sys
import typing

import click
import yaml

from . import TEMPLATE_FOLDER_PATH
from .yaml_utils import read_yaml_key
from .yaml_utils import write_yaml_value


class Configuration:
    """
    Base object created to store in file the configuration used in babylon
    """

    def __init__(self, logger: logging.Logger, config_directory: pathlib.Path):
        self.config_dir = config_directory
        self.logger = logger
        if not self.config_dir.exists():
            self.logger.warning("No config folder existing - Creating it.")
            shutil.copytree(TEMPLATE_FOLDER_PATH / "config_template", self.config_dir)
            self.deploy = self.config_dir.absolute() / "deployments/deploy.yaml"
            self.platform = self.config_dir.absolute() / "platforms/platform.yaml"
            self.plugins: typing.List[typing.Any] = []
            self.save_config()
            return
        self.deploy = pathlib.Path(str(read_yaml_key(self.config_dir / "config.yaml", "deploy")))
        self.platform = pathlib.Path(str(read_yaml_key(self.config_dir / "config.yaml", "platform")))
        self.plugins = read_yaml_key(self.config_dir / "config.yaml", "plugins") or []

    def get_active_plugins(self) -> typing.Generator[typing.Any, pathlib.Path, None]:
        """
        Yields all activated plugins path
        """
        for _p in self.plugins:
            if _p['active']:
                yield _p['name'], pathlib.Path(_p['path'])

    def get_available_plugin(self) -> typing.Generator[str, None, None]:
        """
        Yields all available plugin names
        """
        for _p in self.plugins:
            yield _p['name']

    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Will activate a given plugin
        :param plugin_name: the plugin to activate
        :return: Did the plugin get activated ?
        """
        for _p in self.plugins:
            if _p['name'] == plugin_name:
                _p['active'] = True
                self.save_config()
                return True
        return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Will deactivate a given plugin
        :param plugin_name: the plugin to deactivate
        :return: Did the plugin get deactivated ?
        """
        for _p in self.plugins:
            if _p['name'] == plugin_name:
                _p['active'] = False
                self.save_config()
                return True
        return False

    def remove_plugin(self, plugin_name: str) -> bool:
        """
        Will remove a given plugin
        :param plugin_name: the plugin to remove
        :return: Did the plugin get removed ?
        """
        plugins = [_p for _p in self.plugins if _p["name"] != plugin_name]
        if len(plugins) == len(self.plugins):
            return False
        self.plugins = plugins
        self.save_config()
        return True

    def add_plugin(self, plugin_path: pathlib.Path) -> typing.Optional[str]:
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
        if not plugin_name:
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
        self.save_config()
        return str(plugin_name)

    def __list_config_folder_files(self, folder_name: str) -> typing.Generator[pathlib.Path, None, None]:
        for root, _, files in os.walk(self.config_dir / folder_name):
            for _f in files:
                _file_name = pathlib.Path(root) / pathlib.Path(_f)
                yield _file_name.absolute()

    def list_deploys(self) -> typing.Generator[pathlib.Path, None, None]:
        """
        List existing deployment configurations
        :return: a list of available deployments names
        """
        return self.__list_config_folder_files("deployments")

    def list_platforms(self) -> typing.Generator[pathlib.Path, None, None]:
        """
        List existing platform configurations
        :return: a list of available platforms names
        """
        return self.__list_config_folder_files("platforms")

    def set_deploy(self, deploy_path: pathlib.Path) -> bool:
        """
        Change configured deployment to the one given
        :param deploy_path: the deployment path
        :return: True if the change was a success
        """
        if not deploy_path.exists():
            self.logger.error(f"{deploy_path} is not an existing deployment")
            return False
        self.deploy = deploy_path.absolute()
        self.save_config()
        return True

    def set_platform(self, platform_path: pathlib.Path) -> bool:
        """
        Change configured platform to the one given
        :param platform_path: the platform path
        :return: True if the change was a success
        """
        if not platform_path.exists():
            self.logger.error(f"{platform_path} is not an existing platform")
            return False
        self.platform = platform_path.absolute()
        self.save_config()
        return True

    def create_deploy(self, deploy_name: str):
        """
        Create a new deployment file from the template and open it with the default text editor
        :param deploy_name: the name of the new deploy
        """
        _target = self.config_dir / "deployments" / f"{deploy_name}.yaml"
        if _target.exists():
            self.logger.error(f"Deployment {deploy_name} already exists")
            return
        _t = shutil.copy(TEMPLATE_FOLDER_PATH / "config_template/deployments/deploy.yaml", _target)
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
        _t = shutil.copy(TEMPLATE_FOLDER_PATH / "config_template/platforms/platform.yaml", _target)
        click.edit(filename=str(_t))

    def edit_deploy(self, deploy_path: pathlib.Path):
        """
        Open a given deployment file with the default text editor
        :param deploy_path: the path of the deployment
        """
        if not deploy_path.exists():
            self.logger.error(f"Deployment {deploy_path} does not exists")
            return
        click.edit(filename=str(deploy_path))

    def edit_platform(self, platform_path: pathlib.Path):
        """
        Open a given platform file with the default text editor
        :param platform_path: the path of the platform
        """
        if not platform_path.exists():
            self.logger.error(f"Platform {platform_path} does not exists")
            return
        click.edit(filename=str(platform_path))

    def save_config(self):
        """
        Save the current config
        """
        _d = {"deploy": str(self.deploy), "platform": str(self.platform), "plugins": self.plugins}
        with open(self.config_dir / "config.yaml", "r") as file:
            _d = {**_d, **(yaml.safe_load(file) or {})}

        if _d.get('locked', False):
            self.logger.error("Current config file is locked and won't be updated.")
            return

        self.logger.debug(f"Saving config:\n{pprint.pformat(_d)}")
        yaml.safe_dump(_d, open(self.config_dir / "config.yaml", "w"))
        return

    def get_deploy_path(self) -> typing.Optional[pathlib.Path]:
        """
        Get path to the current deployment file
        :return: path to the current deployment file
        """
        if self.deploy:
            return self.deploy if self.deploy.is_absolute() else self.config_dir / self.deploy
        return None

    def get_platform_path(self) -> typing.Optional[pathlib.Path]:
        """
        Get path to the current platform file
        :return: path to the current platform file
        """
        if self.platform:
            return self.platform if self.platform.is_absolute() else self.config_dir / self.platform
        return None

    def get_deploy_var(self, var_name: str) -> typing.Optional[object]:
        """
        Read a key value from the current deployment file
        :param var_name: the key to read
        :return: the value of the key in the deployment file if exists else None
        """
        _path: pathlib.Path = self.get_deploy_path()
        if not _path.exists():
            return None
        return read_yaml_key(_path, var_name)

    def get_platform_var(self, var_name: str) -> typing.Optional[typing.Any]:
        """
        Read a key value from the current platform file
        :param var_name: the key to read
        :return: the value of the key in the platform file if exists else None
        """
        _path: pathlib.Path = self.get_platform_path()
        if not _path.exists():
            return None
        return read_yaml_key(_path, var_name)

    def set_deploy_var(self, var_name: str, var_value: typing.Any) -> None:
        """
        Set key value in current deployment configuration file
        :param var_name: the key to set
        :param var_value: the value to assign
        """
        _path: pathlib.Path = self.get_deploy_path()
        if not _path.exists():
            return
        write_yaml_value(_path, var_name, var_value)

    def set_platform_var(self, var_name: str, var_value: typing.Any) -> None:
        """
        Set key value in current platform configuration file
        :param var_name: the key to set
        :param var_value: the value to assign
        """
        _path: pathlib.Path = self.get_platform_path()
        if not _path.exists():
            return
        write_yaml_value(_path, var_name, var_value)

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

    def __str__(self) -> str:
        _ret: typing.List[str] = ["Configuration:", f"  dir: {self.config_dir}", f"  deployment: {self.deploy}"]
        with open(self.get_deploy_path(), "r") as _file:
            for k, v in yaml.safe_load(_file).items():
                _ret.append(f"    {k}: {v}")
        _ret.append(f"  platform: {self.platform}")
        with open(self.get_platform_path(), "r") as _file:
            for k, v in yaml.safe_load(_file).items():
                _ret.append(f"    {k}: {v}")
        _ret.append("  plugins:")
        for plugin in self.plugins:
            state = "[x]" if plugin.get('active') else "[ ]"
            _ret.append(f"    {state} {plugin['name']}: {plugin['path']}")
        return "\n".join(_ret)
