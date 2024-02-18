import uuid
import yaml
import os
import json
import logging
import re
import sys
import jmespath
import requests

from pathlib import Path
from hvac import Client
from collections import defaultdict
from typing import Any
from typing import List
from typing import Optional
from mako.template import Template
from Babylon.services.blob import blob_client
from Babylon.utils.yaml_utils import yaml_to_json
from .configuration import Configuration
from .working_dir import WorkingDir
from Babylon.config import config_files
from Babylon.config import get_settings_by_context
from ruamel.yaml import YAML

logger = logging.getLogger("Babylon")

STORE_STRING = "datastore"
TEMPLATES_STRING = "templates"
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
        self.hvac_client = None
        self.pwd = Path.cwd()
        workingdir_path = self.pwd
        config_path = self.pwd / "config"
        self.context_id: str = ""
        self.environ_id: str = ""
        self.server_id: str = ""
        self.tenant_id: str = ""
        self.organization_name: str = ""
        self.dry_run = False
        self.is_verbose = True
        self.working_dir = WorkingDir(workingdir_path)
        self.configuration = Configuration(config_path)
        self.data_store: defaultdict[str, Any] = defaultdict()
        self.AZURE_SCOPES = {
            "graph": "https://graph.microsoft.com/.default",
            "default": "https://management.azure.com/.default",
            "powerbi": "https://analysis.windows.net/powerbi/api/.default",
            "csm_api": "",
        }
        self.reset_data_store()

    def check_environ(self, list_to_check: list):
        vars = list_to_check
        checkers = [k in os.environ for k in vars]
        response = dict(zip(vars, checkers))
        for i, k in response.items():
            if not k:
                logger.error("You can not perform this command")
                logger.error(f"{i} environment variable is missing")
            else:
                if "SERVICE" in i:
                    self.set_server_id()
                if "ORG_NAME" in i and "TOKEN":
                    self.set_org_name()
        if not all(checkers):
            sys.exit(1)

    def set_configuration(self, configuration_path: Path):
        self.configuration = Configuration(config_directory=configuration_path)

    def set_working_dir(self, working_dir_path: Path):
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

    def get_data_from_store(self, data_path: List[str]) -> Any:
        """
        Will look up a data from a given data path and return it
        :param data_path: the path to the data to get
        :return: the value of the data or None if it is not existent
        """
        if not len(data_path):
            raise KeyError("Require at least one component for the data path")

        r = self.convert_data_query(f"{PATH_SYMBOL}{STORE_STRING}{PATH_SYMBOL}" + ".".join(data_path))
        if r is None:
            return False
        return r

    def printable_store(self) -> str:
        return json.dumps(self.data_store, indent=2, default=str)

    def get_data_from_key(self, resource_id: str, keys: list) -> Any:
        config_dir = self.configuration.config_dir
        file_path = (config_dir / f"{self.configuration.context_id}.{self.configuration.environ_id}.{resource_id}.yaml")
        _commented_yaml_loader = YAML()
        try:
            with file_path.open(mode="r") as file:
                _y = _commented_yaml_loader.load(file) or {}
                if len(keys) == 1:
                    _value = _y[self.configuration.context_id][keys[-1]]
                else:
                    _value = _y[self.configuration.context_id][keys[-len(keys)]][keys[-1]]
                return _value
        except OSError:
            return

    def convert_template_path(self, query) -> str:
        check_regex = re.compile(f"{PATH_SYMBOL}"
                                 f"({TEMPLATES_STRING})"
                                 f"{PATH_SYMBOL}"
                                 f"(.+)")
        match_content = check_regex.match(query)
        if not match_content:
            return None
        a, b = match_content.groups()
        templates_path = self.working_dir.original_template_path.absolute().as_posix()
        templates_path += b
        return templates_path

    def convert_data_query(self, query: str, params: dict = {}) -> Any:
        extracted_content = self.extract_value_content(query)
        if not extracted_content:
            logger.debug(f"  '{query}' -> no conversion applied")
            return None

        _type, resource, key_name = extracted_content
        if _type == STORE_STRING:
            logger.debug(f"    Detected parameter type '{_type}' with query '{query}'")
            _value = jmespath.search(key_name, self.data_store)
        else:
            self.set_context(params["context"])
            self.set_environ(params["platform"])
            # self.configuration.set_context(params['context'])
            # self.configuration.set_environ(params['platform'])
            _value = self.configuration.get_var(resource_id=_type, var_name=key_name)
        return _value

    @staticmethod
    def extract_value_content(value: Any) -> Optional[tuple[str, Optional[str], str]]:
        """
        Extract interesting information from a given value
        :param value: Value of the parameter to extract
        :return: None if value has no interesting info else element, filepath, and query
        """

        if not isinstance(value, str):
            return None

        SEARCH_FILES = "|".join(config_files)
        check_regex = re.compile(f"{PATH_SYMBOL}"
                                 f"({SEARCH_FILES}|{STORE_STRING}|{TEMPLATES_STRING})"
                                 f"(?:(?<={STORE_STRING})\\[(.+)])?"
                                 f"{PATH_SYMBOL}"
                                 f"(.+)")

        # Regex groups captures :
        # 1 : Element to query : platform/deploy/workdir/secrets
        # 2 : File path to query in case of a working dir
        # 3 : jmespath query to apply

        match_content = check_regex.match(value)
        if not match_content:
            return None
        return match_content.groups()

    def fill_template(self, template_file: Path, data: dict[str, Any] = {}) -> str:
        """
        Fills a template with environment data using mako template engine
        https://docs.makotemplates.org/en/latest/syntax.html
        :param template_file: Input template file path
        :type template_file: str
        :return: filled template
        """
        template = Template(filename=str(template_file.absolute()), strict_undefined=True)
        context = dict()
        config_dir = self.configuration.config_dir
        for k in config_files:
            context[k] = get_settings_by_context(
                config_dir=config_dir,
                resource=k,
                context_id=self.context_id,
                environ_id=self.environ_id,
            )
        result = template.render(**data, cosmotech=context, datastore=self.data_store)
        if template_file.suffix in [".yaml", ".yml"]:
            result = yaml_to_json(result)
        if template_file.suffix in [".json"]:
            result = json.dumps(json.loads(result))
        return result

    def fill_specification(self, data: str):
        result = data.replace("{{", "${").replace("}}", "}")
        t = Template(text=result, strict_undefined=True)
        values_file = Path().cwd() / "variables.yaml"
        babyvars = dict()
        if values_file.exists():
            babyvars = yaml.safe_load(values_file.open())
        payload = t.render(**babyvars)
        payload_json = yaml_to_json(payload)
        payload_dict: dict = json.loads(payload_json)
        return payload_dict

    def set_context(self, context_id):
        self.context_id = context_id
        self.configuration.set_context(context_id)

    def set_environ(self, environ_id):
        self.environ_id = environ_id
        self.configuration.set_environ(environ_id)

    def set_org_name(self):
        org_name = os.environ.get("BABYLON_ORG_NAME")
        self.organization_name = org_name
        self.tenant_id = self.get_organization_secret(org_name, "tenant")

    def set_server_id(self):
        self.server_id = os.environ.get("BABYLON_SERVICE")
        try:
            client = Client(url=f"{self.server_id}", token=os.environ.get("BABYLON_TOKEN"))
            self.hvac_client = client
        except Exception as e:
            logger.error(e)

    def get_organization_secret(self, organization_name: str, name: str):
        data = self.hvac_client.read(path=f"organization/{organization_name}")
        if data is None:
            logger.error(f"Message: organization {self.organization_name} not found")
            sys.exit(1)
        result = data["data"][name]
        return result

    def get_env_babylon(self, name: str, environ_id: str = ""):
        env_id = environ_id or self.environ_id
        data = self.hvac_client.read(path=f"{self.organization_name}/{self.tenant_id}/babylon/{env_id}/{name}")
        if data is None:
            return None
        return data["data"]["secret"]

    def get_global_secret(self, resource: str, name: str):
        data = self.hvac_client.read(path=f"{self.organization_name}/{self.tenant_id}/global/{resource}/{name}")
        if data is None:
            return None
        return data["data"]["secret"]

    def get_users_secrets(self, email: str, scope: str):
        data = self.hvac_client.read(path=f"{self.organization_name}/{self.tenant_id}/users/{email}/{scope}")
        if data:
            return data["data"]
        return None

    def set_users_secrets(self, email: str, scope: str, cached: dict):
        self.hvac_client.write(
            path=f"{self.organization_name}/{self.tenant_id}/users/{email}/{scope}",
            **cached,
        )

    def get_platform_secret(self, platform: str, resource: str, name: str):
        data = self.hvac_client.read(
            path=f"{self.organization_name}/{self.tenant_id}/platform/{platform}/{resource}/{name}")
        if data is None:
            return None
        return data["data"]["secret"]

    def get_project_secret(self, organization_id: str, workspace_key: str, name: str):
        prefix = f"{self.organization_name}/{self.tenant_id}/projects/{self.context_id}"
        schema = f"{prefix}/{self.environ_id}/{organization_id}/{workspace_key}/{name}".lower()
        data = self.hvac_client.read(path=schema)
        if data is None:
            return None
        return data["data"]["secret"]

    def get_access_token_with_refresh_token(self, username: str = None, internal_scope: str = None):
        email = username or self.configuration.get_var(resource_id="azure", var_name="email")
        cli_client_id = self.configuration.get_var(resource_id="azure", var_name="cli_client_id")
        data = self.get_users_secrets(email, internal_scope)
        if data is None:
            return None
        encrypted_refresh_token = data["token"]
        encoding_key = os.environ.get("BABYLON_ENCODING_KEY")
        if encoding_key is None:
            logger.info("BABYLON_ENCODING_KEY is missing")
            sys.exit(1)
        decryoted_token = self.working_dir.decrypt_content(encoding_key, encrypted_refresh_token)
        response = requests.post(
            url=f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
            data=dict(
                client_id=cli_client_id,
                scope=f"{self.AZURE_SCOPES[internal_scope]} offline_access",
                grant_type="refresh_token",
                refresh_token=decryoted_token.decode("utf-8"),
            ),
        )
        response_json = response.json()
        if "refresh_token" not in response_json:
            return None
        token_encrypt = self.working_dir.encrypt_content(
            encoding_key=encoding_key,
            content=bytes(response_json["refresh_token"], encoding="utf-8"),
        )
        self.set_users_secrets(email, internal_scope, dict(token=token_encrypt.decode("utf-8")))
        return response_json["access_token"]

    def get_state_from_vault_by_platform(self, platform: str):
        resources = config_files
        organization_name = os.environ.get("BABYLON_ORG_NAME", "")
        tenant_id = self.tenant_id
        response_parsed = dict()
        for r in resources:
            response = self.hvac_client.read(path=f"{organization_name}/{tenant_id}/babylon/config/{platform}/{r}")
            if not response:
                logger.info(f"{organization_name}/{tenant_id}/babylon/config/babylon/{platform} not found")
                sys.exit(1)
            response_parsed.setdefault(r, dict(response["data"].items()))
        return response_parsed

    def store_state_in_local(self, state: dict):
        state_dir = Path().home() / ".config/cosmotech/babylon"
        if not state_dir.exists():
            state_dir.mkdir(parents=True, exist_ok=True)
        s = state_dir / f"state.{self.context_id}.{self.environ_id}.yaml"
        s.write_bytes(data=yaml.dump(state).encode("utf-8"))

    def store_state_in_cloud(self, state: dict):
        s = f"{state['id']}/state.{self.context_id}.{self.environ_id}.yaml"
        account_secret = self.get_platform_secret(platform=self.environ_id, resource="storage", name="account")
        state_blob = blob_client(state=state, account_secret=account_secret).get_blob_client(container="babylon-states",
                                                                                             blob=s)
        if state_blob.exists():
            state_blob.delete_blob()
        state_blob.upload_blob(data=yaml.dump(state).encode("utf-8"))

    def get_state_from_local(self, context_id: str = None, platform_id: str = None):
        state_dir = Path().home() / ".config/cosmotech/babylon"
        context_id = context_id or self.context_id
        platform_id = platform_id or self.environ_id
        state_file = state_dir / f"state.{context_id}.{platform_id}.yaml"
        if not state_file.exists():
            return None
        state_data = yaml.safe_load(state_file.open())
        return state_data

    def get_state_from_cloud(self, state: dict) -> dict:
        if not state.get("id"):
            return state
        s = f"{state['id']}/state.{self.context_id}.{self.environ_id}.yaml"
        account_secret = self.get_platform_secret(platform=self.environ_id, resource="storage", name="account")
        state_blob = blob_client(state=state, account_secret=account_secret).get_blob_client(container="babylon-states",
                                                                                             blob=s)
        if not state_blob.exists():
            return state
        if state_blob.exists():
            data = yaml.load(state_blob.download_blob().readall(), Loader=yaml.SafeLoader)
        return data

    def get_state_id(self):
        state_local = self.get_state_from_local()
        if not state_local:
            state_local = dict()
        if not state_local.get("id"):
            state_local.setdefault("id", str(uuid.uuid4()))
            self.store_state_in_local(state_local)
            return state_local.get("id")
        state_cloud = self.get_state_from_cloud(state_local)
        if not state_cloud:
            state_cloud = dict()
        if not state_cloud.get("id"):
            state_cloud.setdefault("id", state_local.get("id"))
        return state_cloud.get("id")

    def store_namespace_in_local(self):
        ns_dir = Path().home() / ".config/cosmotech/babylon"
        if not ns_dir.exists():
            ns_dir.mkdir(parents=True, exist_ok=True)
        s = ns_dir / "namespace.yaml"
        ns = dict(context=self.context_id, platform=self.environ_id)
        s.write_bytes(data=yaml.dump(ns).encode("utf-8"))

    def get_namespace_from_local(self):
        ns_dir = Path().home() / ".config/cosmotech/babylon"
        ns_file = ns_dir / "namespace.yaml"
        if not ns_file.exists():
            logger.error(f"{ns_file} not found")
            logger.error("The context and the platform are not set. \
                         Please set the platform using the 'namespace use' command.")
            sys.exit(1)

        ns_data = yaml.load(ns_file.open("r"), Loader=yaml.SafeLoader)
        self.context_id = ns_data.get("context")
        self.environ_id = ns_data.get("platform")
        return ns_data
