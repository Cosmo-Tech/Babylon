import logging

from click import command
from click import argument
from click import option
from click import Path

import pathlib

from ...utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@argument("source_file", type=Path(exists=True, readable=True, file_okay=True, dir_okay=False, path_type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)))
@option("-o", "--override", is_flag=True, help="Should override already encrypted file")
def encrypt_file(source_file: pathlib.Path, override: bool):
    """Encrypt given SOURCE_FILE"""
    wd = Environment().working_dir
    with open(source_file, "rb") as _f:
        content = _f.read()
    target_file = source_file.parent / (source_file.name + ".encrypt")
    encrypted_file = wd.encrypt_file(target_file, content, override)
    logger.info(f"File was encrypted as {encrypted_file}")
