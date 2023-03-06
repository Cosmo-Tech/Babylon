import json
import logging
import pprint
import subprocess

from click import argument
from click import command

from ...utils.decorators import requires_external_program
from ...utils.decorators import timing_decorator
from ...utils.response import CommandResponse
from ...utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")


@command()
@requires_external_program('kubectl')
@argument("workflow")
@require_platform_key("k8s_context")
@require_platform_key("k8s_namespace")
@timing_decorator
def get_workflow_pods(workflow: str, k8s_context: str, k8s_namespace: str) -> CommandResponse:
    """Get pods information for the given WORKFLOW"""
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
