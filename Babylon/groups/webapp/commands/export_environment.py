import logging
import json

from click import command
from click import option

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")

CONFIG_DATA_QUERIES = {
    "AZURE_TENANT_ID": "%platform%azure_tenant_id",
    "APP_REGISTRATION_CLIENT_ID": "%deploy%webapp_registration_id",
    "COSMOTECH_API_SCOPE": "%platform%api_scope",
    "ORGANIZATION_ID": "%deploy%organization_id",
    "WORKSPACE_ID": "%deploy%workspace_id",
    "APPLICATION_INSIGHTS_INSTRUMENTATION_KEY": "%deploy%webapp_insights_instrumentation_key",
    "ENABLE_APPLICATION_INSIGHTS": "%deploy%webapp_enable_insights"
}

@command()
@option("-o",
        "--output",
        "output_file",
        help="File to which content should be outputted (json-formatted)",
        default="config.json")
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the output file path be relative to Babylon working directory ?")
def export_environment(output_file: str,
                       use_working_dir_file: bool = False) -> CommandResponse:
    """Export webapp configuration in a json file"""
    env = Environment()
    config_data = {k: env.convert_data_query(query) for k, query in CONFIG_DATA_QUERIES.items()}
    if use_working_dir_file:
        output_file = env.working_dir.get_file(output_file)
    with open(output_file, "w") as _f:
        json.dump(config_data, _f, indent=4)
    return CommandResponse.success()
