import click

from Babylon.main import main
from Babylon.utils.macro import Macro


def test_macro_init():
    """Testing macro"""
    with click.Context(main):
        Macro("test").step(["--tests", "config", "display"])


def test_macro_then():
    """Testing macro"""
    with click.Context(main):
        m = Macro("test").then(lambda m: {"test": "data"}, store_at="data")
    assert m.env.convert_data_query("%datastore%data.test") == "data"


def test_macro_iterate():
    """Testing macro"""
    with click.Context(main):
        m = Macro("test")
        m.env.store_data(["list"], ["hello", "world"])
        m.iterate("%datastore%list", ["--tests", "config", "deployment", "set-variable", "test", "%datastore%item"])
    assert m.env.convert_data_query("%deploy%test") == "world"
