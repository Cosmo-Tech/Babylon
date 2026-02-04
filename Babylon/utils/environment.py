import os
import sys
from base64 import b64decode
from collections import defaultdict
from json import loads
from logging import getLogger
from pathlib import Path

from azure.storage.blob import BlobServiceClient
from flatten_json import flatten
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException
from mako.template import Template
from yaml import SafeLoader, YAMLError, dump, load, safe_load

from Babylon.utils import ORIGINAL_CONFIG_FOLDER_PATH, ORIGINAL_TEMPLATE_FOLDER_PATH
from Babylon.utils.working_dir import WorkingDir
from Babylon.utils.yaml_utils import yaml_to_json

logger = getLogger(__name__)

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
        self.remote = False
        self.pwd = Path.cwd()
        self.blob_client = None
        self.state_id: str = ""
        self.context_id: str = ""
        self.environ_id: str = ""
        self.server_id: str = ""
        self.tenant_id: str = ""
        self.original_template_path = ORIGINAL_TEMPLATE_FOLDER_PATH / "working_dir" / ".templates"
        self.dry_run = False
        self.is_verbose = True
        self.AZURE_SCOPES = {
            "graph": "https://graph.microsoft.com/.default",
            "default": "https://management.azure.com/.default",
            "powerbi": "https://analysis.windows.net/powerbi/api/.default",
            "csm_api": "",
        }
        self.state_dir = ORIGINAL_CONFIG_FOLDER_PATH
        self.working_dir = WorkingDir(working_dir_path=self.pwd)
        self.variable_files: list[Path] = []

    def get_variables(self):
        merged_data, duplicate_keys = self.merge_yaml_files(self.variable_files)
        if len(duplicate_keys) > 0:
            for key, files in duplicate_keys.items():
                logger.error(
                    f"  [bold red]✘[/bold red] The key [bold cyan]'{key}'[/bold cyan]"
                    f" is duplicated in variable files {' and '.join(files)}"
                )
            sys.exit(1)
        else:
            merged_data["secret_powerbi"] = ""
            merged_data["github_secret"] = ""
            return merged_data

    def get_ns_from_text(self, content: str):
        t = Template(text=content, strict_undefined=True)
        variables = self.get_variables()
        payload = t.render(**variables)
        payload_dict = safe_load(payload)
        remote: bool = payload_dict.get("remote", self.remote)
        self.remote = remote
        if remote:
            self.set_blob_client()

    def fill_template(self, data: str, state: dict = None, ext_args: dict = None):
        result = data.replace("{{", "${").replace("}}", "}")
        t = Template(text=result, strict_undefined=True)
        variables = self.get_variables()
        flattenstate = {}
        if ext_args:
            variables.update(ext_args)
        if state:
            flattenstate = flatten(state.get("services", {}), separator=".")
        payload = t.render(**variables, services=flattenstate)
        payload_json = yaml_to_json(payload)
        payload_dict = loads(payload_json)
        return payload_dict

    def set_context(self, context_id):
        self.context_id = context_id

    def set_environ(self, environ_id):
        self.environ_id = environ_id

    def set_state_id(self, state_id: str):
        self.state_id = state_id

    def set_blob_client(self):
        try:
            storage_name = os.getenv("STORAGE_NAME", "").strip()
            account_secret = os.getenv("ACCOUNT_SECRET", "").strip()
            if not storage_name and not account_secret:
                raise EnvironmentError("Missing environment variables: 'STORAGE_NAME' and 'ACCOUNT_SECRET'")
            connection_str = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={storage_name};"
                f"AccountKey={account_secret};"
                f"EndpointSuffix=core.windows.net"
            )
            self.blob_client = BlobServiceClient.from_connection_string(connection_str)
        except Exception as e:
            logger.error(f"  [bold red]✘[/bold red] Failed to initialize BlobServiceClient: {e}")
            sys.exit(1)

    def get_config_from_k8s_secret_by_tenant(self, tenant: str):
        response_parsed = {}
        try:
            config.load_kube_config()
        except ConfigException as e:
            logger.error("\n  [bold red]✘[/bold red] Failed to load kube config")
            logger.error(f"  [red]Reason:[/red] {e}")
            logger.info("\n [bold white]💡 Troubleshooting:[/bold white]")
            logger.info("  • Ensure your kubeconfig file is valid")
            logger.info("  • Set your context: [cyan]kubectl config use-context <context-name>[/cyan]")
            sys.exit(1)
        try:
            v1 = client.CoreV1Api()
            secret = v1.read_namespaced_secret(name="keycloak-babylon", namespace=tenant)
        except ApiException:
            logger.error("\n  [bold red]✘[/bold red] Resource Not Found")
            logger.error(
                f"  Secret [green]keycloak-babylon[/green] could not be found in namespace [green]{tenant}[/green]"
            )
            logger.info("\n [bold white]💡 Troubleshooting:[/bold white]")
            logger.info("  • Please ensure your kubeconfig is valid")
            logger.info("  • Check that your context is correctly set [cyan]kubectl config current-context[/cyan]")
            logger.info("  • You can set context using [cyan]kubectl config use-context <context-name>[/cyan]")
            sys.exit(1)
        except Exception:
            logger.error(
                "  [bold red]✘[/bold red] Failed to connect to the Kubernetes cluster: "
                "'Cluster may be down, kube-apiserver unreachable'"
            )
            sys.exit(1)
        if secret.data:
            for key, value in secret.data.items():
                decoded_value = b64decode(value).decode("utf-8")
                response_parsed[key] = decoded_value
        else:
            logger.warning(f"  [yellow]⚠[/yellow] Secret 'keycloak-babylon' in namespace '{tenant}' has no data")
        return response_parsed

    def store_state_in_local(self, state: dict):
        state_file = f"state.{self.context_id}.{self.environ_id}.{self.state_id}.yaml"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        s = self.state_dir / state_file
        state["files"] = self.working_dir.files_to_deploy
        s.write_bytes(data=dump(state).encode("utf-8"))

    def store_state_in_cloud(self, state: dict):
        state_file = f"state.{self.context_id}.{self.environ_id}.{self.state_id}.yaml"
        state_container = self.blob_client.get_container_client(container="babylon-states")
        if not state_container.exists():
            state_container.create_container()
        state_blob = self.blob_client.get_blob_client(container="babylon-states", blob=state_file)
        if state_blob.exists():
            state_blob.delete_blob()
        state_blob.upload_blob(data=dump(state).encode("utf-8"))

    def list_remote_states(self) -> list[str]:
        """Liste les noms des fichiers de state présents dans le container Azure."""
        try:
            self.set_blob_client()
            container_client = self.blob_client.get_container_client(container="babylon-states")
            # On filtre pour ne prendre que les fichiers state.*.yaml
            blobs = container_client.list_blobs(name_starts_with="state.")
            return [b.name for b in blobs if b.name.endswith(".yaml")]
        except Exception as e:
            logger.error(f"  [bold red]✘[/bold red] Impossible de lister les states distants: {e}")
            return []
    
    def get_state_from_local(self):
        state_file = self.state_dir / f"state.{self.context_id}.{self.environ_id}.{self.state_id}.yaml"
        if not state_file.exists():
            return {
                "context": self.context_id,
                "id": self.state_id,
                "tenant": self.environ_id,
                "remote": self.remote,
                "services": {
                    "api": {
                        "organization_id": "",
                        "solution_id": "",
                        "workspace_id": "",
                    },
                    "webapp": {
                        "webapp_name": "",
                        "webapp_url": "",
                    },
                },
            }
        state_data = load(state_file.open("r"), Loader=SafeLoader)
        return state_data

    def get_state_from_cloud(self) -> dict:
        s = f"state.{self.context_id}.{self.environ_id}.{self.state_id}.yaml"
        state_blob = self.blob_client.get_blob_client(container="babylon-states", blob=s)
        exists = state_blob.exists()
        if not exists:
            return {
                "context": self.context_id,
                "id": self.state_id,
                "tenant": self.environ_id,
                "remote": self.remote,
                "services": {
                    "api": {
                        "organization_id": "",
                        "solution_id": "",
                        "workspace_id": "",
                    },
                    "webapp": {
                        "webapp_name": "",
                        "webapp_url": "",
                    },
                },
            }
        data = load(state_blob.download_blob().readall(), Loader=SafeLoader)
        return data

    def store_namespace_in_local(self):
        ns_dir = self.state_dir
        if not ns_dir.exists():
            ns_dir.mkdir(parents=True, exist_ok=True)
        s = ns_dir / "namespace.yaml"
        ns = {"state_id": self.state_id, "context": self.context_id, "tenant": self.environ_id}
        s.write_bytes(data=dump(ns).encode("utf-8"))
        self.set_state_id(state_id=self.state_id)
        self.set_context(context_id=self.context_id)
        self.set_environ(environ_id=self.environ_id)

    def get_namespace_from_local(self, context: str = "", tenant: str = "", state_id: str = ""):
        ns_file = self.state_dir / "namespace.yaml"
        if not ns_file.exists():
            logger.error(f" [bold red]✘[/bold red] [cyan]{ns_file}[/cyan] not found")
            logger.info("  Run the following command to set your active namespace:")
            logger.info("  [cyan]babylon namespace use <tenant-name>[/cyan]")
            sys.exit(1)

        ns_data = safe_load(ns_file.open("r").read())
        if ns_data:
            self.context_id = context or ns_data.get("context", "")
            self.environ_id = tenant or ns_data.get("tenant", "")
            self.state_id = state_id or ns_data.get("state_id", "")
            self.set_state_id(state_id=self.state_id)
            return ns_data

    def retrieve_config(self):
        """Retrieve configuration. First checks environment variables; if missing, fallback to Kubernetes secret."""
        required_env_vars = {
            "API_URL": "API_URL",
            "CLIENT_ID": "CLIENT_ID",
            "CLIENT_SECRET": "CLIENT_SECRET",
            "TOKEN_URL": "TOKEN_URL",
        }
        missing_vars = [var for var in required_env_vars if var not in os.environ]
        if not missing_vars:
            logger.info("  [dim]→ Loading configuration from environment variables...[/dim]")
            return {
                "api_url": os.environ[required_env_vars["API_URL"]],
                "client_id": os.environ[required_env_vars["CLIENT_ID"]],
                "client_secret": os.environ[required_env_vars["CLIENT_SECRET"]],
                "token_url": os.environ[required_env_vars["TOKEN_URL"]],
            }
        # Log missing env vars
        logger.info("  [dim]→ Loading configuration from Kubernetes secret... [/dim]")
        return self.get_config_from_k8s_secret_by_tenant(self.environ_id)

    def retrieve_state_func(self):
        if self.remote:
            state = self.get_state_from_cloud()
        else:
            state = self.get_state_from_local()
        return state

    def set_variable_files(self, variable_files_updated: list[Path]):
        self.variable_files = variable_files_updated

    def load_yaml_file(self, file_path: Path):
        with open(file_path, "r") as file:
            try:
                return safe_load(file) or {}
            except YAMLError as e:
                logger.error(f"  [bold red]✘[/bold red] File '{file_path}' is not a valid YAML file. Details: {str(e)}")
                sys.exit(1)

    def merge_yaml_files(self, file_paths: list[Path]):
        merged_data = {}
        keys_tracker = defaultdict(list)

        for file_path in file_paths:
            if not file_path.endswith(".yaml"):
                logger.error(f"  [bold red]✘[/bold red] File '{file_path}' is not a valid YAML file.")
                sys.exit(1)
            if os.path.getsize(file_path) == 0:
                logger.error(f"  [bold red]✘[/bold red] File '{file_path}' is empty.")
                sys.exit(1)

            data = self.load_yaml_file(file_path)

            for key in data:
                if key in merged_data:
                    keys_tracker[key].append(file_path)
                else:
                    keys_tracker[key] = [file_path]

                merged_data[key] = data[key]

        # Check for duplicate keys
        duplicate_keys = {key: files for key, files in keys_tracker.items() if len(files) > 1}

        return merged_data, duplicate_keys
