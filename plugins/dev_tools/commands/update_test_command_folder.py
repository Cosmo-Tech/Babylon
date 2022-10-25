import logging
import pathlib
import sys

from click import command

from Babylon.main import main
from Babylon.utils import BABYLON_PATH
from .tests_todo import command_tree

logger = logging.getLogger("Babylon")


def initialize_tests(tree, parent_folder: pathlib.Path):
    for k, v in tree.items():
        _k_path = parent_folder / k
        if v:
            if not _k_path.exists():
                logger.info(f"Creating folder {_k_path}")
                _k_path.mkdir(parents=True)
            initialize_tests(v, _k_path)
        else:
            if not _k_path.exists():
                logger.info(f"Creating file {_k_path}")
                f = _k_path.open("x")
                f.close()


@command()
def update_test_command_folder():
    """Will update the test folder with missing files for new commands"""
    tree = command_tree(main)
    initialize_tests(tree, BABYLON_PATH.parent / "tests/commands")
