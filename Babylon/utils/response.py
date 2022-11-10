from typing import Any
from typing import Optional
from typing import Generator
from click import Context
from click import get_current_context


class CommandResponse():
    """Contains command, status and data output from a command return value
    """

    STATUS_OK = 0
    STATUS_ERROR = 1

    def __init__(self, status_code: int = 0, data: Optional[dict[str, Any]] = None) -> None:
        self.status_code = status_code
        self.data = data
        ctx = get_current_context()
        self.command = self._extract_command(ctx)
        self.params = ctx.params

    def _extract_command(self, ctx: Context):

        def gen_group(contx: Context) -> Generator[Context, Any, Any]:
            ctx = contx
            while ctx:
                yield ctx
                ctx: Optional[Context] = ctx.parent

        return reversed([contx.command.name for contx in gen_group(ctx) if ctx.command.name])

    def to_dict(self) -> dict[str, Any]:
        return {"command": self.command, "params": self.params, "status_code": self.status_code, "data": self.data}

    def __str__(self) -> str:
        return "\n".join([
            f"Command: {' '.join(self.command)}",
            "\n".join([f"  -  {key}: {param}" for key, param in self.params.items()]),
            f"Status code: {self.status_code}", "Return value:",
            str(self.data)
        ])
