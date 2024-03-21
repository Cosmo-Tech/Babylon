import pandas as pd
import plotly.offline as pyo
import plotly.graph_objs as go
import plotly.express as px

from logging import getLogger
from click import File, argument, command
from Babylon.commands.abba.common import dataframe_to_dict
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.commands.api.scenarioruns.services.scenariorun_api_svc import ScenarioRunService

logger = getLogger("Babylon")


def get_scenariorun_status(service_state: dict, azure_token) -> dict:
    """Use the babylon scenario run services to get the status of a scenario run.

    Args:
        service_state (dict): Dictionary of state
        azure_token (dict): 

    Returns:
        dict: Request response
    """
    service = ScenarioRunService(state=service_state, azure_token=azure_token)
    response = service.status()
    if response is None:
        logger.error(f"Failed to get status of {service_state['api']['scenariorun_id']}")
    return response.json()


def summarize(data: dict, report_number: int):
    """Summarize the results of a simulation run

    Args:
        data (dict): Dictionary with results.
        report_number (int): An incremental id used to identify and name name the reports.

    Returns:
        DataFrame: Dataframe with some descriptive statistics
    """
    df = pd.DataFrame.from_records(data['nodes'])[['containerName', 'startTime', 'endTime']]
    df['startTime'] = pd.to_datetime(df['startTime'])
    df['endTime'] = pd.to_datetime(df['endTime'])
    df['duration'] = (df['endTime'] - df['startTime']).dt.total_seconds()
    logger.info(f"Report {report_number} generated")
    return df


def generate_report(summary_df: pd.DataFrame, detailed: list):
    """Generate an html report from the status of a series of simulation runs

    Args:
        summary_df (DataFrame): A dataframe with the summary statistics of runs
        detailed (list): List of traces to create the plots
    """
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


@command()
@injectcontext()
@pass_azure_token("csm_api")
@retrieve_state
@argument("input", type=File('r'))
@argument("var_types", type=File('r'))
def check(state: dict, azure_token: str, input: str, var_types: str) -> CommandResponse:
    """Check the status of running simulations and save results to disk.

    Args:
        input (Any): Table with details of the simulations
    """
    # read file provided as argument and run api calls
    input_types = {k: v for k, v in (line.rstrip().split("\t") for line in var_types)}
    df = pd.read_csv(input, sep="\t", na_filter=False)
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
        if not (pd.isnull(start_time) or pd.isnull(end_time)):
            df.loc[i, 'duration'] = (end_time - start_time).total_seconds()
        if response.get('phase') == "Succeeded":
            detailed_data.append(summarize(response, i))
        else:
            logger.info(f"Scenariorun {entry.get('scenariorunId')} has phase {response.get('phase')}")
    generate_report(df, detailed_data)
    return CommandResponse.success()
