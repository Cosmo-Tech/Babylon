import json
import logging
import pprint
import subprocess

from click import argument
from click import command
from click import pass_context

from ....utils.decorators import requires_external_program
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("workflow")
@requires_external_program('kubectl')
@timing_decorator
def get_workflow_pods(ctx, workflow) -> CommandResponse:
    """Get pods information for the given WORKFLOW"""
    k8s_context, k8s_namespace = ctx.obj
    subprocess.check_output(['kubectl', 'config', 'use-context', k8s_context])
    r = json.loads(
        subprocess.check_output([
            'kubectl', 'get', 'pod', '-n', k8s_namespace, '-l', f'workflows.argoproj.io/workflow={workflow}', '-o',
            'json'
        ],
                                stderr=subprocess.DEVNULL))
    items = r['items']
    logger.info(pprint.pformat(items))
    return CommandResponse.success()
