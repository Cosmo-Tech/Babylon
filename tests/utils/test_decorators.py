import time
import logging
from unittest.mock import patch
from pathlib import Path
import pytest
import click
import Babylon.utils.decorators as deco
from Babylon.utils.environment import Environment
from Babylon.utils.working_dir import WorkingDir
from Babylon.utils.configuration import Configuration


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


def test_allow_dry_run():
    """Test decorators"""
    @deco.allow_dry_run
    def my_func(dry_run: bool = False) -> bool:
        return dry_run
    env = Environment(None, None)
    env.dry_run = True
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        assert my_func()


def test_working_dir_yaml():
    """Test decorators"""
    @deco.working_dir_requires_yaml_key("config.yaml", "deploy")
    def my_func():
        pass
    env = Environment(None, WorkingDir(
        Path("tests/environments/Default"), logging))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()


def test_working_dir_yaml_fail():
    """Test decorators"""
    @deco.working_dir_requires_yaml_key("config.yaml", "thisKeyDoesNotExist")
    def my_func():
        pass
    env = Environment(None, WorkingDir(
        Path("tests/environments/Default"), logging))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(click.Abort):
        my_func()


def test_working_dir_requires_file():
    """Test decorators"""
    @deco.working_dir_requires_file("config.yaml")
    def my_func():
        pass
    env = Environment(None, WorkingDir(
        Path("tests/environments/Default"), logging))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()


def test_working_dir_requires_file_fail():
    """Test decorators"""
    @deco.working_dir_requires_file("thisDoesNotExists.yaml")
    def my_func():
        pass
    env = Environment(None, WorkingDir(
        Path("tests/environments/Default"), logging))
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(click.Abort):
        my_func()


def test_requires_program_does_not_exists():
    """Test decorators"""
    @deco.requires_external_program("thisDoesNotExists")
    def my_func():
        pass
    ctx = click.Context(click.Command('cmd'))
    with ctx, pytest.raises(click.Abort):
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
    def my_func():
        pass
    env = Environment(Configuration(config_directory=
        Path("tests/environments/Default"), logger=logging), None)
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(click.Abort):
        my_func()

def test_require_platform_key_ok():
    """Test decorators"""
    @deco.require_platform_key("platform")
    def my_func():
        pass
    env = Environment(Configuration(config_directory=
        Path("tests/environments/Default"), logger=logging), None)
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(click.Abort):
        my_func()

def test_require_deploy_key_fail():
    """Test decorators"""
    @deco.require_deployment_key("thisDoesNotExists")
    def my_func():
        pass
    env = Environment(Configuration(config_directory=
        Path("tests/environments/Default"), logger=logging), None)
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx, pytest.raises(click.Abort):
        my_func()

def test_require_deploy_key_ok():
    """Test decorators"""
    @deco.require_deployment_key("api_url")
    def my_func():
        pass
    env = Environment(Configuration(config_directory=
        Path("tests/environments/Default"), logger=logging), None)
    ctx = click.Context(click.Command('cmd'), obj=env)
    with ctx:
        my_func()
