import json
import os
import re
import sys
import uuid
import yaml
import logging
import requests

from pathlib import Path
from hvac import Client
from mako.template import Template
from cryptography.fernet import Fernet
from flatten_json import flatten
from Babylon.config import config_files
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError

from Babylon.utils import ORIGINAL_TEMPLATE_FOLDER_PATH
from Babylon.utils.working_dir import WorkingDir
from Babylon.utils.yaml_utils import yaml_to_json

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
        self.pwd = Path.cwd()
        self.hvac_client = None
        self.blob_client = None
        self.state_id: str = ""
        self.context_id: str = ""
        self.environ_id: str = ""
        self.server_id: str = ""
        self.tenant_id: str = ""
        self.organization_name: str = ""
        self.original_template_path = (ORIGINAL_TEMPLATE_FOLDER_PATH / "working_dir/.templates")
        self.dry_run = False
        self.is_verbose = True
        self.AZURE_SCOPES = {
            "graph": "https://graph.microsoft.com/.default",
            "default": "https://management.azure.com/.default",
            "powerbi": "https://analysis.windows.net/powerbi/api/.default",
            "csm_api": "",
        }
        self.working_dir = WorkingDir(working_dir_path=self.pwd)

    def get_variables(self):
        variables_file = self.pwd / "variables.yaml"
        vars = dict()
        if variables_file.exists():
            logger.debug(f"Loading variables from {variables_file}")
            vars = yaml.safe_load(variables_file.open()) or dict()
        return vars

    def get_ns_from_text(self, content: str):
        result = content.replace("services", "")
        t = Template(text=result, strict_undefined=True)
        vars = self.get_variables()
        payload = t.render(**vars)
        payload_dict = yaml.safe_load(payload)
        context_id = payload_dict.get("context", "")
        state_id = payload_dict.get("state_id", "")
        if not state_id:
            logger.error("state id is mandatory")
            sys.exit(1)
        plt_obj = payload_dict.get("platform", {})
        platform_id = plt_obj.get("id", "")
        if not platform_id:
            logger.error("platform id is mandatory")
            sys.exit(1)
        platform_url = plt_obj.get("url", "")
        if not platform_url:
            logger.error("url is mandatory")
            sys.exit(1)
        self.set_state_id(state_id=state_id)
        self.set_context(context_id=context_id)
        self.set_environ(environ_id=platform_id)
        self.set_server_id()
        self.set_org_name()
        self.set_blob_client()
        return platform_url

    def fill_template(self, data: str, state: dict = None, ext_args: dict = None):
        result = data.replace("{{", "${").replace("}}", "}")
        t = Template(text=result, strict_undefined=True)
        vars = self.get_variables()
        flattenstate = dict()
        if ext_args:
            vars.update(ext_args)
        if state:
            flattenstate = flatten(state.get("services", {}), separator=".")
        payload = t.render(**vars, services=flattenstate)
        payload_json = yaml_to_json(payload)
        payload_dict = json.loads(payload_json)
        return payload_dict

    def convert_template_path(self, query) -> str:
        check_regex = re.compile(f"{PATH_SYMBOL}"
                                 f"({TEMPLATES_STRING})"
                                 f"{PATH_SYMBOL}"
                                 f"(.+)")
        match_content = check_regex.match(query)
        if not match_content:
            return None
        a, b = match_content.groups()
        templates_path = self.original_template_path.absolute().as_posix()
        templates_path += b
        return templates_path

    def check_environ(self, list_to_check: list):
        vars = list_to_check
        checkers = [k in os.environ for k in vars]
        response = dict(zip(vars, checkers))
        for i, k in response.items():
            if not k:
                logger.error(f"{i} environment variable is missing")
            else:
                if "SERVICE" in i:
                    self.set_server_id()
                if "ORG_NAME" in i and "TOKEN":
                    self.set_org_name()
        if not all(checkers):
            sys.exit(1)

    def set_context(self, context_id):
        self.context_id = context_id

    def set_environ(self, environ_id):
        self.environ_id = environ_id

    def set_state_id(self, state_id: str):
        self.state_id = state_id

    def set_org_name(self):
        self.organization_name = os.environ.get("BABYLON_ORG_NAME")
        self.tenant_id = self.get_organization_secret(self.organization_name, "tenant")

    def set_server_id(self):
        self.server_id = os.environ.get("BABYLON_SERVICE")
        try:
            client = Client(url=f"{self.server_id}", token=os.environ.get("BABYLON_TOKEN"))
            self.hvac_client = client
        except Exception as e:
            logger.error(e)

    def set_blob_client(self):
        try:
            state = self.get_state_from_vault_by_platform(self.environ_id)
            storage_name = state["azure"]["storage_account_name"]
            account_secret = self.get_platform_secret(self.environ_id, resource="storage", name="account")
            prefix = f"DefaultEndpointsProtocol=https;AccountName={storage_name}"
            connection_str = (f"{prefix};AccountKey={account_secret};EndpointSuffix=core.windows.net")
            self.blob_client = BlobServiceClient.from_connection_string(connection_str)
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

    def decrypt_content(encoding_key: bytes, content: bytes) -> bytes:
        if not content:
            return b""
        try:
            decoder = Fernet(encoding_key)
            data = decoder.decrypt(content)
        except Exception:
            logger.error("Could not decrypt content, wrong key ?")
            return b""
        return data

    def get_access_token_with_refresh_token(self, username: str = None, internal_scope: str = None):
        state = self.get_state_from_vault_by_platform(self.environ_id)
        cli_client_id = state["azure"]["cli_client_id"]
        data = self.get_users_secrets(username, internal_scope)
        if data is None:
            return None
        encrypted_refresh_token = data["token"]
        encoding_key = os.environ.get("BABYLON_ENCODING_KEY")
        if encoding_key is None:
            logger.info("BABYLON_ENCODING_KEY is missing")
            sys.exit(1)
        decryoted_token = self.decrypt_content(encoding_key, encrypted_refresh_token)
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
        self.set_users_secrets(username, internal_scope, dict(token=token_encrypt.decode("utf-8")))
        return response_json["access_token"]

    def get_state_from_vault_by_platform(self, platform: str):
        resources = config_files
        organization_name = os.environ.get("BABYLON_ORG_NAME", "")
        tenant_id = self.tenant_id
        response_parsed = dict()
        for r in resources:
            response = self.hvac_client.read(path=f"{organization_name}/{tenant_id}/babylon/config/{platform}/{r}")
            if not response:
                logger.error(f"platform id '{platform}' not found in vault service")
                sys.exit(1)
            response_parsed.setdefault(r, dict(response["data"].items()))
        return response_parsed

    def store_mtime_in_state(self, state: dict):
        state["files"] = self.working_dir.files_to_deploy
        return state

    def store_state_in_local(self, state: dict):
        state_dir = Path().home() / ".config/cosmotech/babylon"
        if not state_dir.exists():
            state_dir.mkdir(parents=True, exist_ok=True)
        s = state_dir / f"state.{self.context_id}.{self.environ_id}.{self.state_id}.yaml"
        state = self.store_mtime_in_state(state)
        s.write_bytes(data=yaml.dump(state).encode("utf-8"))

    def store_state_in_cloud(self, state: dict):
        s = f"state.{self.context_id}.{self.environ_id}.{self.state_id}.yaml"
        try:
            state_blob = self.blob_client.get_blob_client(container="babylon-states", blob=s)
        except ResourceNotFoundError:
            logger.debug("Container 'babylon-states' not found. Creating it...")
            self.blob_client.create_container("babylon-states")
            state_blob = self.blob_client.get_blob_client(container="babylon-states", blob=s)
        if state_blob.exists():
            state_blob.delete_blob()
        state_blob.upload_blob(data=yaml.dump(state).encode("utf-8"))

    def get_state_from_local(self):
        state_dir = Path().home() / ".config/cosmotech/babylon"
        state_file = state_dir / f"state.{self.context_id}.{self.environ_id}.{self.state_id}.yaml"
        if not state_file.exists():
            return dict()
        state_data = yaml.load(state_file.open("r"), Loader=yaml.SafeLoader)
        return state_data

    def get_state_from_cloud(self, state: dict) -> dict:
        if not state.get("id"):
            return state
        self.state_id = state.get("id")
        s = f"state.{self.context_id}.{self.environ_id}.{self.state_id}.yaml"
        state_blob = self.blob_client.get_blob_client(container="babylon-states", blob=s)
        if not state_blob.exists():
            return state
        if state_blob.exists():
            data = yaml.load(state_blob.download_blob().readall(), Loader=yaml.SafeLoader)
        return data

    def get_state_id(self):
        id = str(uuid.uuid4())
        state_local = self.get_state_from_local()
        if not state_local:
            state_local = dict(id="")
        if not state_local.get("id", ""):
            state_local["id"] = id
            return state_local.get("id")
        state_cloud = self.get_state_from_cloud(state_local)
        if not state_cloud:
            state_cloud = dict(id="")
        if state_local and not state_cloud.get("id", ""):
            state_cloud["id"] = state_local.get("id", "") or id
        return state_cloud.get("id")

    def store_namespace_in_local(self):
        ns_dir = Path().home() / ".config/cosmotech/babylon"
        if not ns_dir.exists():
            ns_dir.mkdir(parents=True, exist_ok=True)
        s = ns_dir / "namespace.yaml"
        ns = dict(state_id=self.state_id, context=self.context_id, platform=self.environ_id)
        s.write_bytes(data=yaml.dump(ns).encode("utf-8"))

    def get_namespace_from_local(self, context: str = "", platform: str = "", state_id: str = ""):
        ns_dir = Path().home() / ".config/cosmotech/babylon"
        ns_file = ns_dir / "namespace.yaml"
        if not ns_file.exists():
            logger.error(f"{ns_file} not found")
            logger.error("The context and the platform are not set. \
                         Please set the platform using the 'namespace use' command.")
            sys.exit(1)

        ns_data = yaml.safe_load(ns_file.open("r").read())
        if ns_data:
            self.context_id = context or ns_data.get("context", "")
            self.environ_id = platform or ns_data.get("platform", "")
            self.state_id = state_id or ns_data.get("state_id", "")
            self.set_state_id(state_id=self.state_id)
            self.set_server_id()
            self.set_org_name()
            self.set_blob_client()

    def retrieve_state_func(self, state_id: str = ""):
        init_state = dict()
        final_state = dict()
        final_state["services"] = dict()
        data_vault = self.get_state_from_vault_by_platform(self.environ_id)
        init_state["services"] = data_vault
        init_state["id"] = state_id or self.get_state_id()
        state_cloud = self.get_state_from_cloud(init_state)
        self.store_state_in_local(state_cloud)
        for section, keys in state_cloud.get("services").items():
            final_state["services"][section] = dict()
            for key, _ in keys.items():
                final_state["services"][section].update({key: state_cloud["services"][section][key]})
                if key in data_vault[section] and data_vault[section][key]:
                    final_state["services"][section].update({key: data_vault[section][key]})
        final_state["id"] = init_state.get("id") or state_cloud.get("id")
        final_state["context"] = self.context_id
        final_state["platform"] = self.environ_id
        return final_state

    def set_ns_from_yaml(self, content: str, state: dict = None, ext_args: dict = None):
        ns = self.fill_template(data=content, state=state, ext_args=ext_args).get("namespace")
        context_id = ns.get("context", "")
        state_id = ns.get("state_id", "")
        plt_obj = ns.get("platform", {})
        platform_id = plt_obj.get("id", "")
        if not platform_id:
            logger.error("platform id is mandatory")
            sys.exit(1)
        platform_url = plt_obj.get("url", "")
        if not platform_url:
            logger.error("url is mandatory")
            sys.exit(1)
        url_ = re.compile(f"https:\\/\\/{platform_id}\\.")
        match_content = url_.match(platform_url)
        if not match_content:
            logger.error("url not match")
            sys.exit(1)
        self.state_id = state_id
        self.set_context(context_id=context_id)
        self.set_environ(environ_id=platform_id)
        self.set_server_id()
        self.set_org_name()
        self.set_blob_client()
        return platform_url
