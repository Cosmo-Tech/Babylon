import json
import pandas as pd
import plotly.offline as pyo
import plotly.graph_objs as go
import plotly.express as px
from logging import getLogger
from typing import Any
from click import argument, command, File
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.commands.api.scenarioruns.service.api import ScenarioRunService
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")

env = Environment()


def dataframe_to_dict(df: pd.DataFrame, input_types: dict) -> list:
    """
    Convert a pandas DataFrame to a list of dictionaries.

    Args:
      df (pandas.DataFrame): The DataFrame to convert.
      input_types (dict): A dictionary mapping parameter names to their types.

    Returns:
      list: A list of dictionaries to be used with the cosmotech-api
    """
    result = []
    for line in df.itertuples():
        d = dict()
        d['organizationId'] = line.organizationId
        d['workspaceId'] = line.workspaceId
        d['id'] = line.id
        d['name'] = line.name
        d['description'] = line.description
        d['runTemplateId'] = line.runTemplateId
        if line.scenarioId:
            d['scenarioId'] = line.scenarioId
        if line.scenariorunId:
            d['scenariorunId'] = line.scenariorunId
        d['parameterValues'] = []
        for parameter_value in input_types:
            d['parameterValues'].append({
                'parameterId': parameter_value,
                'value': getattr(line, parameter_value),
                'varType': input_types[parameter_value]
            })
        result.append(d)
    return result


@command()
@injectcontext()
@pass_azure_token("csm_api")
@output_to_file
@argument("input", type=File('r'))
@argument("var_types", type=File('r'))
@retrieve_state
def run(state: Any, azure_token: str, input: str, var_types: str) -> CommandResponse:
    """Run a series of simulations

    Args:
      input (str): Table with details of the simulations
      var_types (str): A table declaring the variable types of columns in input
    """
    df = pd.read_csv(input, sep='\t')
    input_types = {k: v for k, v in (line.rstrip().split("\t") for line in var_types)}
    df['scenarioId'] = ""
    df['scenariorunId'] = ""
    rows = dataframe_to_dict(df, input_types)
    for i, entry in enumerate(rows):
        # create scenario
        service_state = state["services"]
        service_state["api"]["organization_id"] = entry.get('organizationId')
        service_state["api"]["workspace_id"] = entry.get("workspaceId")
        spec = dict()
        spec["payload"] = json.dumps(entry)
        scenario_service = ScenarioService(state=service_state, azure_token=azure_token, spec=spec)
        response = scenario_service.create()
        if response is None:
            logger.error(f"Creating {entry['name']} failed")
            continue
        scenario = response.json()
        logger.info(f"Scenario {scenario['id']} creation was posted")
        df.loc[i, 'scenarioId'] = scenario['id']
        # run scenario
        scenario_service.state["api"]["scenario_id"] = scenario["id"]
        response = scenario_service.run()
        if response is None:
            logger.error(f"Failed run {scenario['id']}")
            continue
        scenario_run = response.json()
        df.loc[i, 'scenariorunId'] = scenario_run['id']
        logger.info(f"Scenario {scenario_run['id']} run posted")
    df.to_csv("back.csv", sep="\t")
    return CommandResponse.success({'rows': rows})


@command()
@injectcontext()
@pass_azure_token("csm_api")
@retrieve_state
@argument("input", type=File('r'))
@argument("var_types", type=File('r'))
def check(state: Any, azure_token: str, input: str, var_types: str) -> CommandResponse:
    """Check the status of running simulations and save results to disk.

    Args:
        input (Any): Table with details of the simulations
    """
    # read file provided as argument and run api calls
    input_types = {k: v for k, v in (line.rstrip().split("\t") for line in var_types)}
    df = pd.read_csv(input, sep='\t')
    rows = dataframe_to_dict(df, input_types)
    service_state = state["services"]
    detailed_data = []
    if 'duration' not in df.columns:
        df['duration'] = ""
    for i, entry in enumerate(rows):
        service_state["api"]["organization_id"] = entry.get('organizationId')
        service_state["api"]["workspace_id"] = entry.get("workspaceId")
        service_state["api"]["scenariorun_id"] = entry.get("scenariorunId")
        response = get_scenariorun_status(service_state, azure_token)
        start_time = pd.to_datetime(response['startTime'])
        end_time = pd.to_datetime(response['endTime'])
        df.loc[i, 'duration'] = (end_time - start_time).total_seconds()
        if response.get('phase') == "Succeeded":
            detailed_data.append(summarize(response, i))
        else:
            logger.info(f"Scenariorun {entry.get('scenariorunId')} has phase {response.get('phase')}")
    generate_report(df, detailed_data)
    return CommandResponse.success()


def get_scenariorun_status(service_state, azure_token):
    # get scenariorun status
    service = ScenarioRunService(state=service_state, azure_token=azure_token)
    response = service.status()
    if response is None:
        logger.error(f"Failed to get status of {service_state['api']['scenariorun_id']}")
    return response.json()


def summarize(data: dict, i: int):
    df = pd.DataFrame.from_records(data['nodes'])[['containerName', 'startTime', 'endTime']]
    df['startTime'] = pd.to_datetime(df['startTime'])
    df['endTime'] = pd.to_datetime(df['endTime'])
    df['duration'] = (df['endTime'] - df['startTime']).dt.total_seconds()
    logger.info(f"Report {i} generated")
    return (df)


def generate_report(summary_df, detailed):
    """Generate summary report from simulation run data."""
    overall_plot = go.Figure(data=[go.Bar(x=summary_df['duration'], y=summary_df['scenariorunId'], orientation='h')])
    overall_plot.update_layout(title='Scenariorun Durations')
    top = pyo.plot(overall_plot, include_plotlyjs=False, output_type='div')
    fig_list = []
    for i, detailed_data in enumerate(detailed):
        fig = px.timeline(detailed_data,
                          title=f"Detailed report for {'i'}",
                          x_start="startTime",
                          x_end="endTime",
                          y="containerName")
        fig.update_traces(text=detailed_data['duration'], textposition='outside')
        fig.update_layout(title="Execution time by step (seconds)", xaxis_title="Time", yaxis_title="Step")
        fig_list.append(pyo.plot(fig, include_plotlyjs=False, output_type='div'))
    # Generate static HTML page (should be viewed online)
    html_content = f"""
  <!DOCTYPE html>
  <html>
  <head>
    <title>Simulation Report</title>
  </head>
  <body>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <h2>Total execution time</h2>
    {top}
    <h2>Execution time by step</h2>
    {"".join(fig_list)}
  </body>
  </html>
  """

    with open("simulation_report.html", "w") as file:
        file.write(html_content)
