import json
import logging

from typing import Any
from typing import Optional
from typing import Callable
from pathlib import Path
from time import sleep
from rich.progress import Progress, SpinnerColumn, TextColumn
from .command_helper import run_command
from .environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


class Macro():
    """
    Handles Macro Command Chaining

    Run a command while allowing method chaining
    ```python
    Macro("My macro")
        .step(["api", "organizations", "get-all"], store_at="orgs")
        .step(["azure", "acr", "list"])
        .dump("report.json")
    ```
    """
    STATUS_OK = 0
    STATUS_ERROR = 1

    def __init__(self, name: str):
        self.name = name
        self._responses: list[dict] = []
        self.env = env
        self._status = self.STATUS_OK

    def step(
        self,
        command_line: list[str],
        is_required: bool = True,
        store_at: Optional[str] = None,
    ) -> "Macro":
        """
        Calls a function within the context of the macro
        :param command_line: command line arguments
        :param store_at: Key at which the data will be stored
        :param is_required: will the Macro go into ERROR if it fails
        :param run_if: run this step only if this argument is True.
        :return: The original macro used for method chaining
        """
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      transient=True) as progress:
            cmd_line = command_line
            print(" ".join(cmd_line))
            progress.add_task(" ".join(cmd_line))
            self.env.is_verbose = False
            res = run_command(cmd_line)
            self._responses.append(res.to_dict())
            if is_required and self._responses[-1]["status_code"]:
                self._status = self.STATUS_ERROR
            if store_at:
                self.env.store_data(store_at.split("."), self._responses[-1]['data'])
        return self

    def then(self, func: Callable[["Macro"], Any], store_at: Optional[str] = None, run_if: bool = True) -> "Macro":
        """
        Calls a function within the context of the macro
        :param func: Function that takes a Macro as argument
        :param store_at: Key at which the result must be stored in the datastore
        :param run_if: Only call the function if run_if is set to True
        :return: The original macro used for method chaining
        """
        if self._status != self.STATUS_OK or not run_if:
            return self
        response = func(self)
        if store_at:
            self.env.store_data(store_at.split("."), response)
        return self

    def iterate(self, datastore_key: str, command_line: list[str]) -> "Macro":
        """
        Iterates a command along a list stored in the datastore
        :param datastore_key: Datastore key at which a list is stored
        :param command_line: command to run
        :return: The original macro used for method chaining
        """
        data = self.env.convert_data_query(datastore_key)
        for item in data:
            self.env.store_data(["item"], item)
            self.step(command_line)
        return self

    def wait(self, delay: int) -> "Macro":
        """
        Waits for delay seconds before continuing
        :param delay: number of seconds to wait for
        :return: The original macro used for method chaining
        """
        if self._status == self.STATUS_ERROR:
            return self
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      transient=True) as progress:
            progress.add_task("Waiting...")
            sleep(delay)
        return self

    def dump(self, output_file: str) -> "Macro":
        """
        Dump command responses data in a json file
        :param output_file: output file path
        :return: The original macro used for method chaining
        """
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
