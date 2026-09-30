from json import dumps
from logging import getLogger
from pathlib import Path

from click import Choice, argument, command, option
from click import Path as ClickPath
from rich.console import Console
from rich.padding import Padding
from rich.syntax import Syntax
from yaml import dump

from Babylon.utils.decorators import _handle_file_output, injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()
console = Console()


@command()
@injectcontext()
@argument("target", type=Choice(["local", "remote"], case_sensitive=False))
@option(
    "-o",
    "--output",
    "output_format",
    type=Choice(["json", "yaml", "wide"], case_sensitive=False),
    default="yaml",
    show_default=True,
    help="Output format. One of: json, yaml, or wide",
)
@option(
    "-f",
    "--file",
    "output_file",
    type=ClickPath(path_type=Path),
    help="Path to the file to save the response",
)
def show_state(target: str, output_format: str, output_file: Path) -> CommandResponse:
    """Display the content of the local or remote state."""
    if target == "local":
        state = env.get_state_from_local()
    else:
        state = env.get_state_from_kubernetes()

    response = CommandResponse.success(data=state)

    if output_file:
        _handle_file_output(response, output_file)

    if output_format == "wide":
        response.print_table()
    else:
        is_json = output_format == "json"
        content = dumps(state, indent=4, ensure_ascii=False) if is_json else dump(state, sort_keys=False)
        lexer = "json" if is_json else "yaml"
        syntax = Syntax(content, lexer, theme="monokai", background_color="default")
        console.print(Padding(syntax, (0, 0, 0, 7)))

    return response
