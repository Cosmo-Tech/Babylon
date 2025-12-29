from logging import getLogger

from click import command

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
def get_contexts() -> CommandResponse:
    """Display the currently active namespace"""
    namespace = env.get_namespace_from_local()
    headers = ["CURRENT", "CONTEXT", "TENANT", "STATE ID"]
    values = ["*", namespace.get("context", ""), namespace.get("tenant", ""), namespace.get("state_id", "")]
    col_widths = [max(len(h), len(v)) + 2 for h, v in zip(headers, values)]
    header_line = "".join(h.ljust(w) for h, w in zip(headers, col_widths))
    value_line = "".join(v.ljust(w) for v, w in zip(values, col_widths))
    print(header_line)
    print(value_line)
    return CommandResponse.success()
