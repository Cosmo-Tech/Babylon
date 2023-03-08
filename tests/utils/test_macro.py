import click

from Babylon.main import main
from Babylon.utils.macro import Macro
import os


def test_macro_init():
    """Testing macro"""
    with click.Context(main):
        m = Macro("test").step(["--tests", "config", "display"])
    assert m._status == m.STATUS_OK


def test_macro_basic():
    """Testing macro"""
    with click.Context(main):
        m = Macro("test") \
            .step(["--tests", "config", "deployment", "set-variable", "hello", "world"]) \
            .step(["--tests", "config", "display"])
    world = m.env.configuration.get_deploy().get("hello")
    m.env.configuration.set_deploy_var("hello", None)
    assert world == "world"
    assert m._status == m.STATUS_OK


def test_macro_then():
    """Testing macro"""
    with click.Context(main):
        m = Macro("test").then(lambda m: {"test": "data"}, store_at="data")
    assert m.env.convert_data_query("%datastore%data.test") == "data"


def test_macro_iterate():
    """Testing macro"""
    os.environ["BABYLON_CONFIG_DIRECTORY"] = "tests/environments/Default"
    with click.Context(main):
        m = Macro("test")
        m.env.store_data(["list"], ["hello", "world"])
        m.iterate("%datastore%list", ["--tests", "config", "deployment", "set-variable", "test", "%datastore%item"])
    assert m.env.convert_data_query("%deploy%test") == "world"
