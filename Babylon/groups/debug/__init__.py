from click import group
from click import pass_context

from .commands import list_commands
from ...utils.decorators import env_requires_yaml_key
from ...utils.decorators import pass_environment


@group()
@pass_environment
@pass_context
@env_requires_yaml_key("deploy.yaml", "k8s_context")
@env_requires_yaml_key("deploy.yaml", "k8s_namespace")
def debug(ctx, environment):
    """Add debug capacities of runs

Requires some keys in `deploy.yaml`: `k8s_context` and `k8s_namespace`"""
    k8s_context = environment.get_yaml_key("deploy.yaml", "k8s_context")
    k8s_namespace = environment.get_yaml_key("deploy.yaml", "k8s_namespace")
    ctx.obj = (k8s_context, k8s_namespace)


for _command in list_commands:
    debug.add_command(_command)
