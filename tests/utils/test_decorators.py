import logging
import time
from pathlib import Path
from unittest.mock import patch

import click
import pytest

import Babylon.utils.decorators as deco
from Babylon.utils.configuration import Configuration
from Babylon.utils.environment import Environment
from Babylon.utils.working_dir import WorkingDir


def test_prepend_doc():
    """Test decorators"""

    @deco.prepend_doc_with_ascii
    def my_func():
        """This is my doc"""

    assert "This is my doc" in (my_func.__doc__ or "")


def test_timing():
    """Test decorators"""

    @deco.timing_decorator
    def my_func():
        time.sleep(1e-2)

    logs: list[str] = []
    with patch("logging.Logger.debug", logs.append):
        my_func()
    assert any("Starting" in log for log in logs)
    assert any("Ending" in log for log in logs)


def test_describe_dry_run():
    """Test decorators"""

    dry_run_description = "Test Description"

    @deco.describe_dry_run(dry_run_description)
    def my_func() -> bool:
        return True

    assert "dry_run" in my_func.__dict__
    assert dry_run_description == my_func.__dict__['dry_run']


def test_working_dir_yaml():
    """Test decorators"""

    @deco.working_dir_requires_yaml_key("config.yaml", "deploy")
    def my_func():
        pass

    env = Environment(None, WorkingDir(Path("tests/environments/Default")))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()


def test_working_dir_yaml_fail():
    """Test decorators"""

    @deco.working_dir_requires_yaml_key("config.yaml", "thisKeyDoesNotExist")
    def my_func():
        pass

    env = Environment(None, WorkingDir(Path("tests/environments/Default")))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(KeyError):
        my_func()


def test_working_dir_requires_file():
    """Test decorators"""

    @deco.working_dir_requires_file("config.yaml")
    def my_func():
        pass

    env = Environment(None, WorkingDir(Path("tests/environments/Default")))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()


def test_working_dir_requires_file_fail():
    """Test decorators"""

    @deco.working_dir_requires_file("thisDoesNotExists.yaml")
    def my_func():
        pass

    env = Environment(None, WorkingDir(Path("tests/environments/Default")))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(FileNotFoundError):
        my_func()


def test_requires_program_does_not_exists():
    """Test decorators"""

    @deco.requires_external_program("thisDoesNotExists")
    def my_func():
        pass

    ctx = click.Context(click.Command('cmd'))
    with ctx, pytest.raises(FileNotFoundError):
        my_func()


def test_requires_program_exists():
    """Test decorators"""

    @deco.requires_external_program("ls")
    def my_func():
        pass

    ctx = click.Context(click.Command('cmd'))
    with ctx:
        my_func()


def test_require_platform_key_fail():
    """Test decorators"""

    @deco.require_platform_key("thisDoesNotExists")
    def my_func(thisDoesNotExists: str):
        pass

    env = Environment(Configuration(config_directory=Path("tests/environments/Default")), None)
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(KeyError):
        my_func()


def test_require_platform_key_ok():
    """Test decorators"""

    @deco.require_platform_key("api_url")
    def my_func(api_url: str):
        pass

    env = Environment(Configuration(config_directory=Path("tests/environments/Default")), None)
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()


def test_require_deploy_key_fail():
    """Test decorators"""

    @deco.require_deployment_key("thisDoesNotExists")
    def my_func(thisDoesNotExists):
        pass

    env = Environment(Configuration(config_directory=Path("tests/environments/Default")), None)
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(KeyError):
        my_func()


def test_require_deploy_key_ok():
    """Test decorators"""

    @deco.require_deployment_key("api_url")
    def my_func(api_url):
        pass

    env = Environment(Configuration(config_directory=Path("tests/environments/Default")), None)
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()
