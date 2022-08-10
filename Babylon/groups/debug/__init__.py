from click import group
from click import pass_context

from .commands import list_commands
from ...utils.decorators import require_platform_key


@group()
@pass_context
@require_platform_key("k8s_context", "k8s_context")
@require_platform_key("k8s_namespace", "k8s_namespace")
def debug(ctx, k8s_context, k8s_namespace):
    """Add debug capacities of runs"""
    ctx.obj = (k8s_context, k8s_namespace)


for _command in list_commands:
    debug.add_command(_command)
