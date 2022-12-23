import time
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import Any

import click
import pytest

import Babylon.utils.decorators as deco
from Babylon.utils.environment import Environment


def test_prepend_doc():
    """Test decorators"""

    @deco.prepend_doc_with_ascii
    def my_func():
        """This is my doc"""

    assert "This is my doc" in my_func.__doc__


def test_timing():
    """Test decorators"""

    @deco.timing_decorator
    def my_func():
        time.sleep(1e-2)

    logs = []
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

    env = Environment()
    env.set_working_dir(Path("tests/environments/Default"))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()


def test_working_dir_yaml_fail():
    """Test decorators"""

    @deco.working_dir_requires_yaml_key("config.yaml", "thisKeyDoesNotExist")
    def my_func():
        pass

    env = Environment()
    env.set_working_dir(Path("tests/environments/Default"))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(KeyError):
        my_func()


def test_working_dir_requires_file():
    """Test decorators"""

    @deco.working_dir_requires_file("config.yaml")
    def my_func():
        pass

    env = Environment()
    env.set_working_dir(Path("tests/environments/Default"))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()


def test_working_dir_requires_file_fail():
    """Test decorators"""

    @deco.working_dir_requires_file("thisDoesNotExists.yaml")
    def my_func():
        pass

    env = Environment()
    env.set_working_dir(Path("tests/environments/Default"))
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


def test_output_to_file():
    """Test decorators"""
    class Response:
        def toJSON(self):
            pass

    @deco.output_to_file
    def my_func() -> Any:
        return Response()

    with patch("builtins.open", mock_open()) as mock_file:
        my_func(output_file="test")
    mock_file.assert_called()
    mock_file.return_value.write.assert_called()


def test_require_platform_key_fail():
    """Test decorators"""

    @deco.require_platform_key("thisDoesNotExists")
    def my_func():
        pass

    env = Environment()
    env.set_configuration(Path("tests/environments/Default"))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(KeyError):
        my_func()


def test_require_platform_key_ok():
    """Test decorators"""

    @deco.require_platform_key("platform")
    def my_func():
        pass

    env = Environment()
    env.set_configuration(Path("tests/environments/Default"))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(KeyError):
        my_func()


def test_require_deploy_key_fail():
    """Test decorators"""

    @deco.require_deployment_key("thisDoesNotExists", "arg_1")
    def my_func(arg_1: str):
        pass

    env = Environment()
    env.set_configuration(Path("tests/environments/Default"))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(KeyError):
        my_func()


def test_require_deploy_key_ok():
    """Test decorators"""

    @deco.require_deployment_key("api_url", insert=False)
    def my_func():
        pass

    env = Environment()
    env.set_configuration(Path("tests/environments/Default"))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()
