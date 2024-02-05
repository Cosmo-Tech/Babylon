from logging import getLogger

from click import command

from Babylon.commands.api.scenarioruns.service.api import ScenarioRunService
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
# @wrapcontext()
# @pass_azure_token('csm_api')
# @get-stuff-from-config
# @option("--o", "organization_id", required=False)
# @option("--o", "scenariorun_id", required=False)
@timing_decorator
def logs(
        # state: dict, spec: dict, azure_token: str, organization_id, scenariorun_id
) -> CommandResponse:
    """
    Get the logs for the scenarioRun
    """
    # if organization_id is None:
    #   organization_id = state['api']['organization_id']

    # if scenariorun_id is None:
    #   scenariorun_id = state['api']['scenariorun_id']

    logger.info(f"Getting logs for scenariorun: 'scenariorun_id'")  # {context['scenariorun_id']}
    service = ScenarioRunService(spec={}, state={
        "api": {"url": "https://dev.api.cosmotech.com", "organization_id": "o-3z188zr63xk",
                "scenariorun_id": "sr-7oq4p0znqy3"}},
                                 azure_token=""
                                 # state=state, spec=spec, azure_token=azure_token
                                 )
    response = service.logs()

    if response is None:
        return CommandResponse.fail()

    run_logs = response.json()

    return CommandResponse.success(run_logs, verbose=True)
