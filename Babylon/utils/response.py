from enum import Enum
from typing import Any
from typing import Optional
from pprint import pformat
from click import Command


class CommandStatus(Enum):
    OK = 0
    ERROR = 1


class CommandResponse():
    """Contains command, status and data output from a command return value
    """

    def __init__(self,
                 command: Command,
                 params: dict[str, Any],
                 status_code: Optional[CommandStatus] = CommandStatus.OK,
                 data: Optional[dict[str, Any]] = None) -> None:
        self.status_code = status_code
        self.data = data
        self.command = command.name
        self.params = params

    def to_dict(self) -> dict[str, Any]:
        return {"command": self.command, "params": self.params, "status_code": self.status_code, "data": self.data}

    def __str__(self) -> str:
        return "\n".join([
            f"Command: {self.command}", "\n".join([f"  -  {key}: {param}" for key, param in self.params.items()]),
            f"Status code: {self.status_code}", "Return value:",
            pformat(self.data)
        ])
