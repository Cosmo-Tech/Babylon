import logging

from click import command
from click import argument
from click import Path

import pathlib

from ...utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@argument("source_file", type=Path(exists=True, readable=True, file_okay=True, dir_okay=False, path_type=Patth(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)))
@argument("target_file", type=Path(writable=True, file_okay=True, dir_okay=False, path_type=Patth(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)))
def decrypt_file(source_file: pathlib.Path, target_file: pathlib.Path):
    """Decrypt given SOURCE_FILE"""
    wd = Environment().working_dir
    content = wd.decrypt_file(source_file)
    with open(target_file, "wb") as _f:
        _f.write(content)
    logger.info(f"File was decrypted as {target_file}")
