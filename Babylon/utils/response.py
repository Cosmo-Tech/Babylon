from typing import Any
from typing import Optional
import json
import logging
from pathlib import Path

from click import get_current_context

logger = logging.getLogger("Babylon")


class CommandResponse():
    """Contains command, status and data output from a command return value
    """

    STATUS_OK = 0
    STATUS_ERROR = 1

    def __init__(self, status_code: int = 0, data: Optional[dict[str, Any]] = None) -> None:
        self.status_code = status_code
        self.data: dict[str, Any] = data or {}
        ctx = get_current_context()
        self.command = ctx.command_path.split(" ")
        self.params = ctx.params

    def to_dict(self) -> dict[str, Any]:
        return {"command": self.command, "params": self.params, "status_code": self.status_code, "data": self.data}

    def __str__(self) -> str:
        return "\n".join([
            f"Command: {' '.join(self.command)}",
            "\n".join([f"  -  {key}: {param}" for key, param in self.params.items()]),
            f"Status code: {self.status_code}", "Return value:",
            str(self.data)
        ])

    def toJSON(self) -> str:
        return json.dumps(self.data, indent=4)

    def dump(self, output_file: str):
        """Dump command response data in a json file"""
        with open(output_file, "w") as _f:
            _f.write(self.toJSON())
        logger.info(f"The JSON response was dumped in file: {output_file}")

    def has_failed(self) -> bool:
        """Checks if command has failed"""
        if self.status_code != self.STATUS_ERROR:
            return False
        return True

    @classmethod
    def fail(cls) -> Any:
        return cls(status_code=CommandResponse.STATUS_ERROR)

    @classmethod
    def success(cls, data: Optional[dict[str, Any]] = None) -> Any:
        return cls(status_code=CommandResponse.STATUS_OK, data=data)


class MacroReport():
    """Contains commands, statuses and data output from macros
    """
    def __init__(self):
        self._commands: dict[str, CommandResponse] = {}

    def addCommand(self, name: str, cmd: CommandResponse):
        self._commands[name] = cmd

    def dump(self, output_file: str):
        """Dump command responses data in a json file"""
        compiled = {k: response.data for k, response in self._commands.items()}
        path = Path(output_file)
        output_path = path
        for idx in range(1, 10000):
            if not output_path.exists():
                break
            output_path = path.with_stem(f"{path.stem}_{idx}")
        with open(output_path, "w") as _f:
            json.dump(compiled, _f, indent=4)
        logger.info(f"Macro report was dumped in file: {output_path}")
