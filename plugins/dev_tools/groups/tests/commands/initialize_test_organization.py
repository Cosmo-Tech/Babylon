import logging
import pathlib

from click import command

from Babylon.main import main
from Babylon.utils import BABYLON_PATH
from .commands_to_test import command_tree

logger = logging.getLogger("Babylon")


def initialize_tests(tree, parent_folder: pathlib.Path):
    for k, v in tree.items():
        _k_path = parent_folder / k
        if v:
            if not _k_path.exists():
                logger.info(f"Creating folder {_k_path}")
                _k_path.mkdir(parents=True)
            initialize_tests(v, _k_path)
            continue
        if not _k_path.exists():
            logger.info(f"Creating file {_k_path}")
            f = _k_path.open("x")
            f.write(" ".join(["babylon", *str(_k_path).split('tests/commands/')[1].split('/')]))
            f.close()


@command()
def initialize_test_organization():
    """Will update the test folder with missing files for new commands"""
    tree = command_tree(main)
    initialize_tests(tree, BABYLON_PATH.parent / "tests/commands")
