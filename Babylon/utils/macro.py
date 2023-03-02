import json
import logging
from typing import Any
from typing import Optional
from pathlib import Path
from time import sleep

from .response import CommandResponse
from .command_helper import run_command
from .environment import Environment

logger = logging.getLogger("Babylon")


class Macro():
    """Handles Macro Command Chaining
    """
    STATUS_OK = 0
    STATUS_ERROR = 1

    def __init__(self, name: str):
        self.name = name
        self._responses: list[CommandResponse] = []
        self.env = Environment()
        self._status = self.STATUS_OK

    def step(self,
             command_line: list[str],
             optional: bool = False,
             store_at: Optional[str] = None,
             run_if: bool = True) -> Any:
        """
        Run a command while allowing method chaining
        Macro()
            .step(["api", "organization", "get-all"])
            .step(["azure", "acr", "list", "-d", "src"])
            .dump("report.json")
        """
        if self._status != self.STATUS_OK or not run_if:
            logger.warning(f"Skipping command {' '.join(command_line)}...")
            return self
        logger.info(f"Running command {' '.join(command_line)}")
        self._responses.append(run_command(command_line))
        if not optional and self._responses[-1].has_failed():
            self._status = self.STATUS_ERROR
            return self
        if store_at:
            self.env.store_data(store_at.split("."), self._responses[-1].to_dict())
        return self

    def wait(self, delay: int):
        """Wait"""
        if self._status == self.STATUS_ERROR:
            return self
        logger.info(f"Waiting {delay}s...")
        sleep(delay)
        return self

    def dump(self, output_file: str):
        """Dump command responses data in a json file"""
        compiled = [{"header": self.name}]
        compiled.extend([response.to_dict() for response in self._responses])
        path = Path(output_file)
        output_path = path
        for idx in range(1, 10000):
            if not output_path.exists():
                break
            output_path = path.with_stem(f"{path.stem}_{idx}")
        with open(output_path, "w") as _f:
            json.dump(compiled, _f, indent=4)
        logger.info(f"Macro report was dumped in file: {output_path}")
