import os

import click
import pytest
from click.testing import CliRunner

import Babylon.utils.decorators as deco
from Babylon.main import main
from Babylon.utils.command_helper import run_command
from Babylon.utils.environment import Environment
from Babylon.utils.macro import Macro
from Babylon.utils.response import CommandResponse


def test_must_success_config_int():
    with click.Context(main):
        result = run_command(["config", "init"])
        assert result.has_success()


def test_must_success_working_dir_complete():
    with click.Context(main):
        result = run_command(["working-dir", "complete"])
        assert result.has_success()


def test_must_success_config_display():
    with click.Context(main):
        result = run_command(["config", "display"])
        assert result.has_success()


def test_must_success_set_deploy_api_url():
    api_url = os.environ["BABYLON_INTEGRATION_API_URL"]
    with click.Context(main):
        result = run_command(["config", "set-variable", "deploy", "api_url", f"{api_url}"])
        assert result.has_success()


def test_must_success_set_platform_api_url():
    api_url = os.environ["BABYLON_INTEGRATION_API_URL"]
    with click.Context(main):
        result = run_command(["config", "set-variable", "platform", "api_url", f"{api_url}"])
        assert result.has_success()


def test_must_success_set_api_scope():
    api_scope = os.environ["BABYLON_INTEGRATION_API_SCOPE"]
    with click.Context(main):
        result = run_command(["config", "set-variable", "platform", "api_scope", f"{api_scope}"])
        assert result.has_success()


def test_must_success_az_login_with_aadapp():
    app_id = os.environ["BABYLON_INTEGRATION_API_AZURE_CLIENT_ID"]
    app_secret = os.environ["BABYLON_INTEGRATION_API_AZURE_CLIENT_SECRET"]
    tenant_id = os.environ["BABYLON_INTEGRATION_API_AZURE_TENANT_ID"]
    with click.Context(main):
        result = run_command(["azure", "login", "-i", f"{app_id}", "-p", f"{app_secret}", "-t", f"{tenant_id}"])
        assert result.has_success()


def test_must_success_organization_get_all():
    with click.Context(main):
        result = run_command(["api", "organization", "get-all"])
        assert result.has_success()


def test_must_success_organization_get_first():
    with click.Context(main):
        result = run_command([
            "api", "organization", "get-all", "--filter", "[0]", "-o",
            "integration/environments/core/API/OUTPUT/organization_get_first.json"
        ])
        assert result.has_success()


def test_must_success_organization_get_by_id():
    with click.Context(main):
        result = run_command(["api", "organization", "get", "%workdir[API/OUTPUT/organization_get_first.json]%id"])
        assert result.has_success()


def test_must_fail_organization_create():
    with click.Context(main):
        result = run_command(["api", "organization", "create", "Babylon integration test"])
        assert result.has_failed()


def test_must_success_organization_create_json():
    with click.Context(main):
        result = run_command([
            "api",
            "organization",
            "create",
            "-i",
            "integration/environments/core/API/INPUT/json/organization.json",
            "Babylon integration test",
            "--select",
        ])
        assert result.has_success()


def test_organization_must_success_get_by_id_json():
    with click.Context(main):
        result = run_command(["api", "organization", "get"])
        assert result.has_success()


@pytest.fixture()
def test_must_fqil_organization_delete_json(args=["-s", "yes"]):
    with click.Context(main):
        result = run_command([
            "api",
            "organization",
            "delete",
            "%deploy%organization_id",
        ])
        assert result.fail()


def test_must_success_organization_security_update_yaml():
    with click.Context(main):
        result = run_command([
            "api",
            "organization",
            "security",
            "update",
            "integration/environments/core/API/INPUT/yaml/test_security.yaml",
        ])
        assert result.has_success()


def test_must_success_organization_delete_json():
    with click.Context(main):
        result = run_command([
            "api",
            "organization",
            "delete",
            "-f",
            "%deploy%organization_id",
        ])
        assert result.has_success()


def test_must_success_organization_create_yaml():
    with click.Context(main):
        result = run_command([
            "api",
            "organization",
            "create",
            "-i",
            "integration/environments/core/API/INPUT/yaml/organization.yaml",
            "Babylon integration test",
            "--select",
        ])
        assert result.has_success()


def test_must_success_organization_security_update_json():
    with click.Context(main):
        result = run_command([
            "api",
            "organization",
            "security",
            "update",
            "integration/environments/core/API/INPUT/json/test_security.json",
        ])
        assert result.has_success()


def test_organization_must_success_get_by_id_yaml():
    with click.Context(main):
        result = run_command(["api", "organization", "get"])
        assert result.has_success()


def test_organization_must_success_get_security():
    with click.Context(main):
        result = run_command(["api", "organization", "security", "get"])
        assert result.has_success()


def test_organization_must_success_get_security_output():
    with click.Context(main):
        result = run_command([
            "api", "organization", "security", "get", "--organization",
            "%workdir[API/OUTPUT/organization_get_first.json]%id", "-o",
            "integration/environments/core/API/OUTPUT/security_get.json"
        ])
        assert result.has_success()


def test_organization_must_fail_get_security_output():
    with click.Context(main):
        result = run_command([
            "api", "organization", "security", "get", "--organization", "boof", "-o",
            "integration/environments/core/API/OUTPUT/security_get.json"
        ])
        assert result.has_failed()


def test_must_success_organization_delete_yaml():
    with click.Context(main):
        result = run_command([
            "api",
            "organization",
            "delete",
            "-f",
            "%deploy%organization_id",
        ])
        assert result.has_success()


def test_must_success_azure_logout():
    with click.Context(main):
        result = run_command(["azure", "logout", "-f"])
        assert result.has_success()


def test_organization_must_fail_get_by_id():
    with click.Context(main):
        result = run_command(["api", "organization", "get", "%workdir[API/OUTPUT/organization_get_first.json]%id"])
        assert result.has_failed()
