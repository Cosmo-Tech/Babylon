import logging
import jmespath

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, output_to_file, wrapcontext
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token
from ruamel.yaml import YAML

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@output_to_file
@pass_powerbi_token()
@option("--report-type", "report_type", type=Choice(["scenario_view", "dashboard_view"]), help="Report Type")
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@argument("report_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def pages(
    context: Any,
    powerbi_token: str,
    report_id: str,
    report_type: str,
    workspace_id: str,
) -> CommandResponse:
    """
    Get info from a powerbi report of a workspace
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/pages"
    response = oauth_request(urls_reports, powerbi_token)
    if response is None:
        logger.info("Report id not found")
        return CommandResponse.fail()
    output_data = response.json()
    pagesnames = jmespath.search("value[?order==`0`]", output_data)
    pagesname = pagesnames[0] if len(pagesnames) else "ReportSection"

    yaml_loader = YAML()
    data_file = env.configuration.config_dir / f"{env.context_id}.{env.environ_id}.powerbi.yaml"
    if not data_file.exists():
        logger.info(f"Config file {env.context_id}.{env.environ_id}.powerbi.yaml not found")
        return CommandResponse.fail()
    yaml_file = data_file
    with yaml_file.open(mode='r') as _f:
        data = yaml_loader.load(_f)
    _view = data[env.context_id][report_type]
    test_match = jmespath.search(f"[?contains(reportId, '{report_id}')]", _view)

    if len(test_match):
        idx = _view.index(test_match[0])
    if pagesname:
        _view[idx]['pageName'] = {"en": f"{pagesname['name']}", "fr": f"{pagesname['name']}"}
    data[env.context_id][report_type][idx] = _view[idx]
    with data_file.open(mode='w+') as _f:
        yaml_loader.dump(data, data_file)
    return CommandResponse.success(output_data, verbose=True)
