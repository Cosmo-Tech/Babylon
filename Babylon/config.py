import os

from glob import glob
from pathlib import Path
from dynaconf import Dynaconf

config_files = [
    'acr', 'adt', 'adx', 'api', 'app', 'keycloak', 'azure', 'babylon', 'github', 'platform', 'powerbi', 'webapp'
]

pwd = Path(os.getcwd())


def get_config_files(config_dir: Path):
    """Retrieve all configuration files from resource"""
    _list = list(map(lambda x: glob(str(config_dir / f"*.*.{x}.yaml")), config_files.sort()))
    response = []
    for item in _list:
        response += item
    return response


def get_settings_by_context(
    config_dir: Path,
    resource: str,
    context_id: str,
    environ_id: str,
):
    """Retrieve all configurations files from platform and resource"""
    _list = glob(str(config_dir / f"*.{environ_id}.{resource}.yaml"))
    _settings = Dynaconf(settings_files=_list)
    try:
        return _settings[context_id]
    except Exception:
        return dict()
