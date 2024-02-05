import logging
import os

from hvac import Client
from click import command
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


@command(name="init")
@wrapcontext()
@pass_hvac_client
def init(hvac_client: Client) -> CommandResponse:
    """
    Initialize Babylon configuration
    """
    if not env.configuration.config_dir.exists():
        os.mkdir("config")
    if not env.working_dir.payload_path.exists():
        os.mkdir(".payload")
    if not env.working_dir.adx_path.exists():
        os.mkdir("adx")
    if not env.working_dir.powerbi_path.exists():
        os.mkdir("powerbi")

    env.configuration.set_configuration_files_from_template(hvac_client=hvac_client,
                                                            template_name=env.environ_id,
                                                            tenant_id=env.tenant_id)
    env.configuration.set_var(resource_id="azure", var_name="tenant_id", var_value=env.tenant_id)
    env.configuration.set_var(resource_id="powerbi", var_name="scenario_view", var_value=None)
    env.configuration.set_var(resource_id="powerbi", var_name="dashboard_view", var_value=None)
    return CommandResponse.success()