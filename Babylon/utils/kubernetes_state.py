"""
Cloud-agnostic Kubernetes Secret state management.

Works with any Kubernetes cluster (AKS, EKS, GKE, KOB/on-prem, …) that is
reachable via the current kubeconfig context.

Secret layout
─────────────
  apiVersion: v1
  kind: Secret
  type: Opaque
  metadata:
    name: <secret_name>
    namespace: <namespace>
  data:
    state.yaml: <base64-encoded YAML string>

The single key inside the secret is always ``STATE_KEY`` ("state.yaml").
"""

import sys
from base64 import b64decode, b64encode
from logging import getLogger

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException
from yaml import dump, safe_load

logger = getLogger(__name__)

# The key name stored inside the Kubernetes Secret's data map.
STATE_KEY = "state.yaml"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_kube_config() -> None:
    """Load kubeconfig, with a clear error message on failure."""
    try:
        config.load_kube_config()
    except ConfigException as exc:
        logger.error("\n  [bold red]✘[/bold red] Failed to load kube config")
        logger.error(f"  [red]Reason:[/red] {exc}")
        logger.info("\n [bold white]💡 Troubleshooting:[/bold white]")
        logger.info("  • Ensure your kubeconfig file is valid")
        logger.info("  • Set your context: [cyan]kubectl config use-context <context-name>[/cyan]")
        sys.exit(1)


def _core_v1() -> client.CoreV1Api:
    """Return a CoreV1Api instance (kubeconfig must already be loaded)."""
    return client.CoreV1Api()


def _encode(data: dict) -> str:
    """Serialise *data* to YAML and return a base64 string (utf-8)."""
    yaml_str = dump(data, allow_unicode=True)
    return b64encode(yaml_str.encode("utf-8")).decode("utf-8")


def _decode(raw: bytes | str) -> dict:
    """Decode a base64 value coming from a Secret's ``data`` field.

    The kubernetes-client already base64-decodes ``data`` values when it
    parses the API response, so *raw* may arrive as plain bytes or as a
    base64 string depending on the client version.  This helper handles
    both cases gracefully.
    """
    if isinstance(raw, (bytes, bytearray)):
        yaml_str = raw.decode("utf-8")
    else:
        # Still base64-encoded (older client versions or raw JSON payload).
        yaml_str = b64decode(raw).decode("utf-8")
    return safe_load(yaml_str) or {}


def _build_secret(namespace: str, secret_name: str, encoded_value: str) -> client.V1Secret:
    """Build a V1Secret object ready for create / replace calls."""
    return client.V1Secret(
        api_version="v1",
        kind="Secret",
        type="Opaque",
        metadata=client.V1ObjectMeta(name=secret_name, namespace=namespace),
        data={STATE_KEY: encoded_value},
    )

# Public API

def store_state_in_kubernetes(namespace: str, secret_name: str, state_data: dict) -> None:
    """Persist *state_data* as a Kubernetes Secret in *namespace*.

    If the secret already exists it is **updated** (replaced) rather than
    causing an error.  The secret type is ``Opaque`` and the state is stored
    under the key ``state.yaml`` as a base64-encoded YAML string.
    """
    _load_kube_config()
    v1 = _core_v1()
    encoded = _encode(state_data)
    secret = _build_secret(namespace, secret_name, encoded)

    try:
        # Check whether the secret exists first.
        v1.read_namespaced_secret(name=secret_name, namespace=namespace)
        # Secret exists → replace it.
        v1.replace_namespaced_secret(name=secret_name, namespace=namespace, body=secret)
        logger.info(
            f"  [green]✔[/green] State secret [cyan]{secret_name}[/cyan] "
            f"updated in namespace [cyan]{namespace}[/cyan]"
        )
    except ApiException as exc:
        if exc.status == 404:
            # Secret does not exist → create it.
            v1.create_namespaced_secret(namespace=namespace, body=secret)
            logger.info(
                f"  [green]✔[/green] State secret [cyan]{secret_name}[/cyan] "
                f"created in namespace [cyan]{namespace}[/cyan]"
            )
        else:
            logger.error(
                f"  [bold red]✘[/bold red] Kubernetes API error while storing state "
                f"(HTTP {exc.status}): {exc.reason}"
            )
            sys.exit(1)
    except Exception as exc:
        logger.error(
            f"  [bold red]✘[/bold red] Failed to connect to the Kubernetes cluster: {exc}"
        )
        sys.exit(1)


def get_state_from_kubernetes(namespace: str, secret_name: str) -> dict | None:
    """Read state from a Kubernetes Secret and return it as a dictionary.

    Returns ``None`` when the secret does not exist so the caller can decide
    whether to initialise a fresh state or raise an error.
    """
    _load_kube_config()
    v1 = _core_v1()

    try:
        secret = v1.read_namespaced_secret(name=secret_name, namespace=namespace)
    except ApiException as exc:
        if exc.status == 404:
            logger.warning(
                f"  [yellow]⚠[/yellow] State secret [cyan]{secret_name}[/cyan] "
                f"not found in namespace [cyan]{namespace}[/cyan]"
            )
            return None
        logger.error(
            f"  [bold red]✘[/bold red] Kubernetes API error while retrieving state "
            f"(HTTP {exc.status}): {exc.reason}"
        )
        sys.exit(1)
    except Exception as exc:
        logger.error(
            f"  [bold red]✘[/bold red] Failed to connect to the Kubernetes cluster: {exc}"
        )
        sys.exit(1)

    if not secret.data or STATE_KEY not in secret.data:
        logger.warning(
            f"  [yellow]⚠[/yellow] State secret [cyan]{secret_name}[/cyan] exists "
            f"but contains no [cyan]{STATE_KEY}[/cyan] key"
        )
        return None

    state = _decode(secret.data[STATE_KEY])
    logger.info(
        f"  [green]✔[/green] State loaded from secret [cyan]{secret_name}[/cyan] "
        f"in namespace [cyan]{namespace}[/cyan]"
    )
    return state
