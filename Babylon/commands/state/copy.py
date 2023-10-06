import os
import shutil
import tempfile
import yaml
import glob
import logging

from typing import Any
from hvac import Client
from pathlib import Path
from click import command, option
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_hvac_client
@wrapcontext()
@option("--to", "to", help="Platform target", required=True)
@inject_context_with_resource({"api": ["workspace_key"]})
def copy(context: Any, hvac_client: Client, to: str) -> CommandResponse:
    """
    Copy state to another platform
    """
    organization_name = os.environ.get('BABYLON_ORG_NAME', '')
    config = env.working_dir.path / "config"
    schema = str(config / f"{env.context_id}.{env.environ_id}.*.yaml")

    files = glob.glob(schema)
    for _file in files:
        resource = _file.split(".")[2]
        _f = Path(_file)
        src = yaml.load(_f.open("r"), Loader=yaml.SafeLoader)
        config_key = src[env.context_id]
        response = hvac_client.read(path=f'{organization_name}/{env.tenant_id}/babylon/config/{to}/{resource}')
        if response is None:
            logger.error(f"{to} platform config not found")
            return CommandResponse.fail()
        for key, value in config_key.items():
            if key in response['data']:
                config_key[key] = response['data'][key] or value
        yaml_file = yaml.dump({env.context_id: config_key})
        tmpf = tempfile.NamedTemporaryFile(mode="w+")
        tmpf.write(yaml_file)
        tmpf.seek(0)
        target = str(config / f"{env.context_id}.{to}.{resource}.yaml")
        shutil.copy(tmpf.name, target)
        tmpf.flush()
        tmpf.close()
    logger.info(f"Successfully copied context: '{env.context_id}' from '{env.environ_id}' to '{to}' platform")
    return CommandResponse.success()
