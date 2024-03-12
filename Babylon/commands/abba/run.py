import json
import pandas as pd

from logging import getLogger
from click import argument, command, File
from Babylon.commands.abba.common import dataframe_to_dict
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.commands.api.scenarios.services.api import ScenarioService
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")

env = Environment()


@command()
@injectcontext()
@pass_azure_token("csm_api")
@output_to_file
@argument("input", type=File('r'))
@argument("var_types", type=File('r'))
@retrieve_state
def run(state: dict, azure_token: str, input: str, var_types: str) -> CommandResponse:
    """Run a series of simulations

    Args:
      input (str): Table with details of the simulations
      var_types (str): A table declaring the variable types of columns in input
    """
    df = pd.read_csv(input, sep="\t", na_filter=False)
    input_types = {k: v for k, v in (line.rstrip().split("\t") for line in var_types)}
    df['scenarioId'] = ""
    df['scenariorunId'] = ""
    rows = dataframe_to_dict(df, input_types)
    for i, entry in enumerate(rows):
        # create scenario
        service_state = state["services"]
        service_state["api"]["organization_id"] = entry.get('organizationId') or service_state["api"]["organization_id"]
        service_state["api"]["workspace_id"] = entry.get("workspaceId") or service_state["api"]["workspace_id"]
        spec = dict()
        spec["payload"] = json.dumps(entry)
        scenario_service = ScenarioService(state=service_state, azure_token=azure_token, spec=spec)
        response = scenario_service.create()
        if response is None:
            logger.error(f"Creating {entry['name']} failed")
            continue
        scenario = response.json()
        logger.info(f"Scenario {scenario['id']} has been created.")
        df.loc[i, 'scenarioId'] = scenario['id']
        # run scenario
        scenario_service.state["api"]["scenario_id"] = scenario["id"]
        response = scenario_service.run()
        if response is None:
            logger.error(f"Failed run {scenario['id']}")
            continue
        scenario_run = response.json()
        df.loc[i, 'scenariorunId'] = scenario_run['id']
        logger.info(f"Scenariorun {scenario_run['id']} has been created.")
    df.to_csv("back.csv", sep="\t")
    return CommandResponse.success({'rows': rows})
