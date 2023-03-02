import click

from Babylon.main import main
from Babylon.utils.macro import Macro


def test_macro_init():
    """Testing macro"""
    ctx = click.Context(main)
    with ctx:
        Macro("test").step(["config", "display"])
