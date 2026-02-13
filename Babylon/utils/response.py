import json
import logging
import pathlib
import shutil
import tempfile
from datetime import datetime
from typing import Any, Optional

import yaml
from click import get_current_context
from rich.console import Console
from rich.pretty import pprint
from rich.table import Table

from .environment import Environment

logger = logging.getLogger(__name__)
console = Console()


class CommandResponse:
    """
    Contains command, status and data output from a command return value
    """

    STATUS_OK = 0
    STATUS_ERROR = 1

    def __init__(self, status_code: int = 0, data: Optional[dict[str, Any]] = None, verbose: bool = False) -> None:
        self.status_code = status_code
        self.data: dict[str, Any] = data or {}
        ctx = get_current_context()
        self.command = ctx.command_path.split(" ")
        self.params = {k: str(v) for k, v in ctx.params.items()}
        if verbose and Environment().is_verbose:
            pprint(self.data)

    def to_dict(self) -> dict[str, Any]:
        return {"command": self.command, "params": self.params, "status_code": self.status_code, "data": self.data}

    def __str__(self) -> str:
        return "\n".join(
            [
                f"Command: {' '.join(self.command)}",
                "\n".join([f"  -  {key}: {param}" for key, param in self.params.items()]),
                f"Status code: {self.status_code}",
                "Return value:",
                str(self.data),
            ]
        )

    def toJSON(self) -> str:
        return json.dumps(self.data, indent=4, ensure_ascii=False)

    def toYAML(self) -> str:
        return yaml.dump(self.data)

    def _get_normalized_items(self) -> list:
        raw_data = self.data
        if isinstance(raw_data, dict):
            items = [raw_data] if "id" in raw_data or "version" in raw_data else list(raw_data.values())
        elif isinstance(raw_data, list):
            items = raw_data
        else:
            items = []
        return [i for i in items if i and isinstance(i, dict)]

    def _is_api_info_type(self, first_item: dict) -> bool:
        version_content = first_item.get("version", {})
        return isinstance(version_content, dict) and "release" in version_content

    def _add_resource_row(self, table: Table, item: dict):
        raw_ts = item.get("create_info", {}).get("timestamp")
        created_at = "N/A"
        if raw_ts:
            dt = datetime.fromtimestamp(raw_ts / 1000.0)
            created_at = dt.strftime("%Y-%m-%d %H:%M")

        table.add_row(str(item.get("id", "N/A")), str(item.get("name", "N/A")), created_at)

    def print_table(self):
        """
        Handles the display of Organization data.
        """

        items = self._get_normalized_items()
        if not items:
            return

        is_api_info = self._is_api_info_type(items[0])
        table = Table(show_header=True, header_style="bold white", box=None, padding=(0, 2), show_edge=False, expand=False)
        if is_api_info:
            table.add_column("PROPERTY")
            table.add_column("VALUE")
            for item in items:
                v = item.get("version", {})
                if isinstance(v, dict):
                    table.add_row("Full Version", v.get("full", "N/A"))
                    table.add_row("Release", v.get("release", "N/A"))
                else:
                    table.add_row("Version", str(v))
        else:
            table.add_column("ID", no_wrap=True)
            table.add_column("NAME")
            table.add_column("CREATED", no_wrap=True)
            for item in items:
                self._add_resource_row(table, item)

        console.print(table)

    def dump_yaml(self, output_file: pathlib.Path):
        """Dump command response data in a yaml file"""
        yaml_file = yaml.dump(self.data)
        tmpf = tempfile.NamedTemporaryFile(mode="w+")
        tmpf.write(yaml_file)
        tmpf.seek(0)
        shutil.copy(tmpf.name, output_file)
        tmpf.flush()
        tmpf.close()
        logger.info(f"  [green]✔[/green] The YAML response was dumped in file [bold]{output_file}[/bold]")

    def dump_json(self, output_file: pathlib.Path):
        """Dump command response data in a json file"""
        with open(output_file, "w") as _f:
            _f.write(self.toJSON())
        logger.info(f"  [green]✔[/green] The JSON response was dumped in file [bold]{output_file}[/bold]")

    def has_failed(self) -> bool:
        """Checks if command has failed"""
        return self.status_code == self.STATUS_ERROR

    @classmethod
    def fail(cls, **kwargs) -> Any:
        return cls(status_code=CommandResponse.STATUS_ERROR, **kwargs)

    @classmethod
    def success(cls, data: Optional[dict[str, Any]] = None, **kwargs) -> Any:
        return cls(status_code=CommandResponse.STATUS_OK, data=data, **kwargs)
