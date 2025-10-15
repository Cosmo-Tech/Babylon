import pathlib

from logging import getLogger
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


def deploy_dataset(namespace: str, file_content: str, deploy_dir: pathlib.Path) -> dict:
  raise NotImplementedError("Not implemented yet.")