import os
import sys
from base64 import b64decode
from collections import defaultdict
from json import loads
from logging import getLogger
from pathlib import Path

from flatten_json import flatten
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException
from mako.template import Template
from yaml import SafeLoader, YAMLError, dump, load, safe_load

from Babylon.utils import ORIGINAL_CONFIG_FOLDER_PATH, ORIGINAL_TEMPLATE_FOLDER_PATH
from Babylon.utils.kubernetes_state import STATE_LABEL_KEY, STATE_LABEL_VALUE, get_state_from_kubernetes, store_state_in_kubernetes
from Babylon.utils.working_dir import WorkingDir
from Babylon.utils.yaml_utils import yaml_to_json

logger = getLogger(__name__)

STORE_STRING = "datastore"
TEMPLATES_STRING = "templates"
PATH_SYMBOL = "%"
NAMESPACE_FILE = "namespace.yaml"


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
    # Azure Blob Storage configuration
    STATE_CONTAINER = "babylon-states"

    def __init__(self):
        self.remote = False
        self.pwd = Path.cwd()
        self.blob_client = None
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

    def _get_active_kubectl_context(self) -> str:
        try:
            from kubernetes.config.kube_config import list_kube_config_contexts

            _, active_context = list_kube_config_contexts()
            return active_context["name"] if active_context else "unknown"
        except Exception:
            return "unknown"

    def _get_babylon_namespace_info(self) -> str:
        ns_file = self.state_dir / NAMESPACE_FILE
        if not ns_file.exists():
            return "[dim]not set[/dim]"
        try:
            ns_data = safe_load(ns_file.open("r").read()) or {}
            babylon_ctx = ns_data.get("context", "")
            babylon_tenant = ns_data.get("tenant", "")
            return (
                f"context=[bold cyan]{babylon_ctx}[/bold cyan]  "
                f"tenant=[bold cyan]{babylon_tenant}[/bold cyan]  "
            )
        except Exception:
            return "[dim]unavailable[/dim]"

    def _load_k8s_secret(self, secret_name: str, tenant: str):
        try:
            v1 = client.CoreV1Api()
            return v1.read_namespaced_secret(name=secret_name, namespace=tenant)
        except ApiException:
            logger.error(f"  [yellow]⚠[/yellow] Secret [green]{secret_name}[/green] could not be found in namespace [green]{tenant}[/green].")
            logger.info("\n [bold white]💡 Troubleshooting:[/bold white]")
            logger.info(f"  • Active kubectl context : [cyan]{self._get_active_kubectl_context()}[/cyan]")
            logger.info(f"  • Active Babylon namespace: {self._get_babylon_namespace_info()}")
            logger.info("  • If the kubectl context is wrong, switch it:")
            logger.info("    [cyan]kubectl config use-context <context-name>[/cyan]")
            logger.info("  • If the Babylon namespace is wrong, switch it:")
            logger.info("    [cyan]babylon namespace use -c <context> -t <tenant>[/cyan]")
            sys.exit(1)
        except Exception:
            logger.error(
                "  [bold red]✘[/bold red] Failed to connect to the Kubernetes cluster: "
                "'Cluster may be down, kube-apiserver unreachable'"
            )
            sys.exit(1)

    def get_config_from_k8s_secret_by_tenant(self, secret_name: str, tenant: str):
        try:
            config.load_kube_config()
        except ConfigException as e:
            logger.error("\n  [bold red]✘[/bold red] Failed to load kube config")
            logger.error(f"  [red]Reason:[/red] {e}")
            logger.info("\n [bold white]💡 Troubleshooting:[/bold white]")
            logger.info("  • Ensure your kubeconfig file is valid")
            logger.info("  • Set your context: [cyan]kubectl config use-context <context-name>[/cyan]")
            sys.exit(1)

        secret = self._load_k8s_secret(secret_name, tenant)

        if not secret.data:
            logger.warning(f"  [yellow]⚠[/yellow] Secret {secret_name} in namespace '{tenant}' has no data")
            return {}

        return {key: b64decode(value).decode("utf-8") for key, value in secret.data.items()}

    def store_state_in_local(self, state: dict):
        state_file = f"state.{self.context_id}.{self.environ_id}.yaml"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        s = self.state_dir / state_file
        s.write_bytes(data=dump(state).encode("utf-8"))

    def store_state_in_kubernetes(self, state: dict, namespace: str = "", secret_name: str = "") -> None:
        """Persist *state* as a Kubernetes Secret.
        """
        ns = namespace or self.environ_id
        name = secret_name or f"babylon-state-{self.context_id}-{self.environ_id}"
        store_state_in_kubernetes(namespace=ns, secret_name=name, state_data=state)

    def get_state_from_kubernetes(self, namespace: str = "", secret_name: str = "") -> dict:
        """Retrieve state from a Kubernetes Secret.

        Returns the stored dictionary, or an empty default state when the
        secret does not exist yet (mirrors the behaviour of
        ``get_state_from_local`` and ``get_state_from_cloud``).
        """
        ns = namespace or self.environ_id
        name = secret_name or f"babylon-state-{self.context_id}-{self.environ_id}"
        result = get_state_from_kubernetes(namespace=ns, secret_name=name)
        if result is None:
            return {
                "context": self.context_id,
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
                    "postgres": {
                        "schema_name": "",
                    },
                },
            }
        return result

    def list_remote_states(self) -> list[str]:
        """List state secret names matching 'babylon-state-*' in the current namespace.

        Uses a server-side label selector so only matching secrets are transferred
        over the wire — no client-side filtering needed.
        """
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            secrets = v1.list_namespaced_secret(
                namespace=self.environ_id,
                label_selector=f"{STATE_LABEL_KEY}={STATE_LABEL_VALUE}",
            )
            return [s.metadata.name for s in secrets.items]
        except Exception as e:
            logger.error(f"  [bold red]✘[/bold red] Failed to list remote states: {e}")
            return []

    def get_state_from_local(self):
        state_file = self.state_dir / f"state.{self.context_id}.{self.environ_id}.yaml"
        if not state_file.exists():
            return {
                "context": self.context_id,
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
                    "postgres": {
                        "schema_name": "",
                    },
                },
            }
        state_data = load(state_file.open("r"), Loader=SafeLoader)
        return state_data

    def store_namespace_in_local(self):
        ns_dir = self.state_dir
        if not ns_dir.exists():
            ns_dir.mkdir(parents=True, exist_ok=True)
        s = ns_dir / NAMESPACE_FILE
        ns = {"context": self.context_id, "tenant": self.environ_id}
        s.write_bytes(data=dump(ns).encode("utf-8"))
        self.set_context(context_id=self.context_id)
        self.set_environ(environ_id=self.environ_id)

    def get_namespace_from_local(self, context: str = "", tenant: str = ""):
        ns_file = self.state_dir / NAMESPACE_FILE
        if not ns_file.exists():
            logger.error(f" [bold red]✘[/bold red] [cyan]{ns_file}[/cyan] not found")
            logger.info("  Run the following command to set your active namespace:")
            logger.info("  [cyan]babylon namespace use <tenant-name>[/cyan]")
            sys.exit(1)

        ns_data = safe_load(ns_file.open("r").read())
        if ns_data:
            self.context_id = context or ns_data.get("context", "")
            self.environ_id = tenant or ns_data.get("tenant", "")
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
        return self.get_config_from_k8s_secret_by_tenant("keycloak-babylon", self.environ_id)

    def retrieve_state_func(self):
        if self.remote:
            state = self.get_state_from_kubernetes()
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
