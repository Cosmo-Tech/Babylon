"""How Babylon authenticates to Kubernetes.

Babylon supports two authentication methods:

  * kubeconfig: uses the local kubeconfig file (~/.kube/config).
  * in-cluster: uses the ServiceAccount token mounted by Kubernetes inside a pod.

The method is selected with BABYLON_K8S_AUTH:

  * "kubeconfig": always use kubeconfig.
  * "incluster": always use the ServiceAccount.
  * "auto" (default): use in-cluster inside a pod, kubeconfig otherwise.

"""

from __future__ import annotations

import os
from collections.abc import Mapping

from kubernetes import config
from kubernetes.config.config_exception import ConfigException

from Babylon.core.errors import InvalidOptionsError, KubernetesAuthError

AUTH_ENV_VAR = "BABYLON_K8S_AUTH"
AUTH_MODES = ("auto", "kubeconfig", "incluster")


def resolve_auth_mode(environ: Mapping[str, str], kube_context: str | None) -> str:
    """Return "kubeconfig" or "incluster" """

    mode = (environ.get(AUTH_ENV_VAR) or "auto").strip().lower()

    if mode not in AUTH_MODES:
        raise InvalidOptionsError(f"{AUTH_ENV_VAR}={mode!r} is invalid. Allowed values are: {', '.join(AUTH_MODES)}")

    if mode != "auto":
        return mode

    # An explicit --kube-context only makes sense with a kubeconfig file.
    in_pod = bool(environ.get("KUBERNETES_SERVICE_HOST"))
    return "incluster" if in_pod and not kube_context else "kubeconfig"


def load_kubernetes_config(kube_context: str | None = None, environ: Mapping[str, str] | None = None) -> str:
    """Load the Kubernetes credentials into the kubernetes client library. Returns the mode used.

    Raises:
        KubernetesAuthError: the credentials for the chosen mode cannot be loaded.
        InvalidOptionsError: BABYLON_K8S_AUTH has an unknown value.
    """
    environ = os.environ if environ is None else environ
    mode = resolve_auth_mode(environ, kube_context)
    try:
        if mode == "incluster":
            config.load_incluster_config()
        else:
            config.load_kube_config(context=kube_context)
    except ConfigException as exc:
        raise KubernetesAuthError(f"Cannot load Kubernetes credentials ({mode}): {exc}") from exc
    return mode
