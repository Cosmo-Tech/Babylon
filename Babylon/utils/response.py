from enum import Enum
from typing import Any
from typing import Optional

from click import Command


class CommandStatus(Enum):
    OK = 0
    ERROR = 1


class CommandResponse():
    """Contains command, status and data output from a command return value
    """

    def __init__(self,
                 command: Command,
                 status_code: Optional[CommandStatus] = CommandStatus.OK,
                 data: Optional[dict[str, Any]] = None) -> None:
        self.status_code = status_code
        self.data = data
        self.command = command

    def to_dict(self) -> dict[str, Any]:
        return {"command": self.command.name, "status_code": self.status_code, "data": self.data}
