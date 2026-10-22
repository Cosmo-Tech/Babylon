"""Tests of Babylon.core.kube (Kubernetes authentication mode)."""

import pytest
from kubernetes import config
from kubernetes.config.config_exception import ConfigException

from Babylon.core import kube
from Babylon.core.errors import InvalidOptionsError, KubernetesAuthError
from Babylon.core.kube import load_kubernetes_config, resolve_auth_mode
from Babylon.utils.environment import Environment

IN_POD = {"KUBERNETES_SERVICE_HOST": "10.0.0.1"}


@pytest.mark.parametrize(
    "environ, kube_context, expected",
    [
        ({}, None, "kubeconfig"),  # laptop: historical behaviour
        (IN_POD, None, "incluster"),  # pod: ServiceAccount
        (IN_POD, "kind-dev", "kubeconfig"),  # explicit --kube-context wins
        ({"BABYLON_K8S_AUTH": "kubeconfig", **IN_POD}, None, "kubeconfig"),
        ({"BABYLON_K8S_AUTH": "incluster"}, None, "incluster"),
        ({"BABYLON_K8S_AUTH": " InCluster "}, None, "incluster"),  # tolerant to case/spaces
        ({"BABYLON_K8S_AUTH": ""}, None, "kubeconfig"),  # empty = auto
    ],
)
def test_resolve_auth_mode(environ, kube_context, expected):
    assert resolve_auth_mode(environ, kube_context) == expected


def test_unknown_mode_is_rejected():
    with pytest.raises(InvalidOptionsError, match="BABYLON_K8S_AUTH"):
        resolve_auth_mode({"BABYLON_K8S_AUTH": "token"}, None)


@pytest.fixture
def loaders(monkeypatch):
    """Replace the kubernetes loaders: record which one is called."""
    calls = []
    monkeypatch.setattr(config, "load_incluster_config", lambda: calls.append(("incluster",)))
    monkeypatch.setattr(config, "load_kube_config", lambda context=None: calls.append(("kubeconfig", context)))
    return calls


def test_load_calls_the_right_loader(loaders):
    assert load_kubernetes_config(environ=IN_POD) == "incluster"
    assert load_kubernetes_config(kube_context="kind-dev", environ=IN_POD) == "kubeconfig"
    assert loaders == [("incluster",), ("kubeconfig", "kind-dev")]


def test_load_failure_becomes_a_babylon_error(monkeypatch):
    def broken():
        raise ConfigException("Service host/port is not set.")

    monkeypatch.setattr(config, "load_incluster_config", broken)
    with pytest.raises(KubernetesAuthError, match="incluster.*Service host/port"):
        load_kubernetes_config(environ={"BABYLON_K8S_AUTH": "incluster"})


def test_environment_client_uses_kube_module(monkeypatch, loaders):
    monkeypatch.setenv("BABYLON_K8S_AUTH", "incluster")
    Environment().get_kubernetes_client()
    assert loaders == [("incluster",)]


def test_environment_client_keeps_cli_behaviour_on_failure(monkeypatch):
    def broken(**_):
        raise KubernetesAuthError("no credentials")

    monkeypatch.setattr(kube, "load_kubernetes_config", broken)
    with pytest.raises(SystemExit) as exc:
        Environment().get_kubernetes_client()
    assert exc.value.code == 1
