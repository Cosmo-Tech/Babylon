import json
import logging
from typing import Any
from typing import Optional
from typing import Callable
from pathlib import Path
from time import sleep
from rich.progress import Progress, SpinnerColumn, TextColumn

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
             store_at: Optional[str] = None,
             is_required: bool = True,
             run_if: bool = True) -> "Macro":
        """
        Run a command while allowing method chaining
        Macro()
            .step(["api", "organization", "get-all"], store_at="orgs")
            .step(["azure", "acr", "list", "-d", "src"])
            .dump("report.json")

        Args:
            command_line (list[str]): command line arguments
            store_at (Optional[str], optional): Key at which the data will be stored. Defaults to None.
            is_required (bool, optional): will the Macro go into ERROR if it fails. Defaults to True.
            run_if (bool, optional): run this step only if this argument is True. Defaults to True.

        Returns:
            Macro: Used for method chaining
        """
        if self._status != self.STATUS_OK or not run_if:
            logger.warning(f"Skipping command {' '.join(command_line)}...")
            return self
        self.env.is_verbose = False
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      transient=True) as progress:
            progress.add_task(' '.join(command_line))
            self.env.is_verbose = False
            self._responses.append(run_command(command_line))
            self.env.is_verbose = True
            if is_required and self._responses[-1].has_failed():
                self._status = self.STATUS_ERROR
                return self
            if store_at:
                self.env.store_data(store_at.split("."), self._responses[-1].to_dict())
        self.env.is_verbose = True
        return self

    def then(self, func: Callable[["Macro"], Any], store_at: Optional[str] = None, run_if: bool = True) -> "Macro":
        """Calls a function within the context of the macro"""
        if self._status != self.STATUS_OK or not run_if:
            logger.warning("Skipping function")
            return self
        response = func(self)
        if store_at:
            self.env.store_data(store_at.split("."), response)
        return self

    def iterate(self, datastore_key: str, command_line: list[str]):
        """Iterates other data in the datastore"""
        data = self.env.convert_data_query(datastore_key)
        for item in data:
            self.env.store_data(["item"], item)
            self.step(command_line)
        return self

    def wait(self, delay: int) -> "Macro":
        """Wait"""
        if self._status == self.STATUS_ERROR:
            return self
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      transient=True) as progress:
            progress.add_task("Waiting...")
            sleep(delay)
        return self

    def dump(self, output_file: str) -> "Macro":
        """Dump command responses data in a json file"""
        compiled = [{"header": self.name}]
        compiled.extend([response.to_dict() for response in self._responses])
        path = Path(output_file)
        output_path = path
        # Get an available filename of the form output_file_xxxx.json
        idx = 1
        while output_path.exists():
            output_path = path.with_stem(f"{path.stem}_{idx}")
            idx += 1
        with open(output_path, "w") as _f:
            json.dump(compiled, _f, indent=4)
        logger.info(f"Macro report was dumped in file: {output_path}")
        return self
