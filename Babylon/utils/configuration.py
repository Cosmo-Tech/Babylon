import pathlib
import logging
import shutil
import subprocess
import sys
import click
import tempfile

from . import ORIGINAL_TEMPLATE_FOLDER_PATH
from hvac import Client
from typing import Any
from typing import Optional
from mako.template import Template
from Babylon.config import config_files
from Babylon.config import pwd
from Babylon.config import get_settings_by_context
from Babylon.utils.yaml_utils import get_file_config_from_keys
from Babylon.utils.yaml_utils import read_yaml_key
from Babylon.utils.yaml_utils import read_yaml_key_from_context
from Babylon.utils.yaml_utils import write_yaml_value_from_context

logger = logging.getLogger("Babylon")


class Configuration:
    """
    Base object created to store in file the configuration used in babylon
    """

    def __init__(self, config_directory: pathlib.Path):
        self.context_id: str = ""
        self.environ_id: str = ""
        self.server_id: str = ""
        self.config_dir = config_directory
        self.plugins = read_yaml_key(self.config_dir / "plugins.yaml", "plugins") or list()

    def initialize(self) -> bool:
        if not self.config_dir.exists():
            logger.error("Configuration folder does not exists.")

        self.plugins: list[dict[str, Any]] = list()
        return True

    def get_active_plugins(self) -> list[(str, pathlib.Path)]:
        """
        Yields all activated plugins path
        """
        return [(_p["name"], pathlib.Path(_p["path"])) for _p in self.plugins if _p.get("active")]

    def get_available_plugin(self) -> list[str]:
        """
        Yields all available plugin names
        """
        return [_p["name"] for _p in self.plugins]

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
        for idx, _p in enumerate(self.plugins):
            if _p['name'] == plugin_name:
                self.plugins.pop(idx)
                self.save_config()
                return True
        return False

    def add_plugin(self, plugin_path: pathlib.Path) -> Optional[str]:
        """
        Will add a plugin to the config given a plugin path
        :param plugin_path: path to the plugin folder to add
        :return: The name of the plugin added, or None if plugin could not be added
        """
        plugin_config_path = plugin_path / "plugin_config.yaml"
        if not plugin_config_path.exists():
            logger.error(f"`{plugin_path}` is not a valid plugin folder")
            return None
        plugin_name = read_yaml_key(plugin_config_path, "plugin_name")
        if plugin_name is None:
            logger.error(f"`{plugin_path}` is not a valid plugin folder, no plugin_name found.")
            return None

        if plugin_name in self.get_available_plugin():
            logger.error(f"`{plugin_name}` is an already existing plugin")
            return None

        requirements_path = plugin_path / "requirements.txt"
        if requirements_path.exists():
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path.absolute())])
            except subprocess.CalledProcessError:
                logger.error(f"Issues while installing requirements for `{plugin_name}`")
                return None

        plugin_entry = dict(name=plugin_name, path=str(plugin_path.absolute()), active=True)
        self.plugins.append(plugin_entry)
        self.save_config()
        return str(plugin_name)

    def get_path(self, resource_id: str, context_id: str = "", environ_id: str = "") -> Optional[pathlib.Path]:
        ctxt_id = context_id or self.context_id
        env_id = environ_id or self.environ_id
        file_path = self.config_dir / f"{ctxt_id}.{env_id}.{resource_id}.yaml"
        if not file_path.exists():
            logger.info(f"You are trying to use {resource_id.upper()} group")
            logger.info(f"With '{env_id}' platform and '{ctxt_id}' context")
            logger.info(f"File configuration: {ctxt_id}.{env_id}.{resource_id}.yaml not found")
            sys.exit(1)
        return file_path

    def set_var(self, resource_id: str, var_name: str, var_value: Any) -> bool:
        """
        Set <key>: <value> after in configuration file
        """
        if not (_path := self.get_path(resource_id)).exists():
            return
        write_yaml_value_from_context(_path, self.context_id, var_name, var_value)

    def get_var(self, resource_id: str, var_name: str, context_id: str = "", environ_id: str = "") -> str:
        ctxt_id = context_id or self.context_id
        env_id = environ_id or self.environ_id
        if not (_path := self.get_path(resource_id, ctxt_id, env_id)).exists():
            return
        return read_yaml_key_from_context(_path, ctxt_id, var_name)

    def create(self, config_type: str):
        """
        Create a new config file from the template and open it with the default text editor
        """
        context_id = self.context_id.lower().strip()
        environ_id = self.environ_id.lower().strip()
        config_type = config_type.lower().strip()

        _target = self.config_dir / f"{context_id}.{environ_id}.{config_type}.yaml"
        if _target.exists():
            logger.info(f"Config file {context_id}.{config_type} already exists")
            return
        template_file = ORIGINAL_TEMPLATE_FOLDER_PATH / f"config_template/{config_type}.yaml"
        if not template_file.exists():
            sys.exit(1)

        content = Template(filename=str(template_file)).render(context_id=context_id)
        text = click.edit(text=content, require_save=True)
        if text is None:
            sys.exit(1)
        tmpf = tempfile.NamedTemporaryFile(mode="w+")
        tmpf.write(text)
        tmpf.seek(0)
        shutil.copy(tmpf.name, _target)

        _ret: list[str] = []
        _ret.append(f"New config file: {context_id}.{environ_id}.{config_type}.yaml 🚀")
        logger.info("\n".join(_ret))

    def set_context(self, context_id):
        self.context_id = context_id

    def set_environ(self, environ_id):
        self.environ_id = environ_id

    def set_configuration_files_from_template(self, hvac_client: Client, template_name: str, tenant_id: str):
        for _k in config_files:
            key = f"{_k}"
            yaml_config_file = self.config_dir / f"{self.context_id}.{template_name}.{_k}.yaml"
            get_file_config_from_keys(
                hvac_client=hvac_client,
                context_id=self.context_id,
                config_file=yaml_config_file,
                tenant_id=tenant_id,
                key_name=key,
                resource=template_name,
            )

        logger.info(f"Context: '{self.context_id}'")
        logger.info(f"Platform: '{self.environ_id}'")
        logger.info("Successfully initialized")

    def __str__(self) -> str:
        _ret: list[str] = ["Configuration:"]
        _ret.append(f"  context: '{self.context_id}'")
        _ret.append(f"  platform: '{self.environ_id}'")
        _ret.append("  plugins: ")
        for plugin in self.plugins:
            state = "[x]" if plugin.get('active') else "[ ]"
            _ret.append(f"    {state} {plugin['name']}: {plugin['path']}")

        _ret.append("  resources: ")
        for config in config_files:
            _settings = get_settings_by_context(pwd / self.config_dir,
                                                resource=config,
                                                context_id=self.context_id,
                                                environ_id=self.environ_id)
            _ret.append(f"    [{config}]")
            for k, v in _settings.items():
                if isinstance(v, dict):
                    _rett: list[str] = [f"      [{k}]"]
                    for m, p in v.items():
                        _rett.append(f"         • {m}: {p}")
                    _ret.append("\n".join(_rett))
                elif isinstance(v, list):
                    _rett: list[str] = [f"      [{k}]"]
                    for m, p in enumerate(v):
                        _rett.append(f"         • {m}: {p}")
                    _ret.append("\n".join(_rett))
                else:
                    _ret.append(f"      • {k}: {v}")
        return "\n".join(_ret)
