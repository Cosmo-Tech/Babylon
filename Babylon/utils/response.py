import logging
import json
import pathlib
import shutil
import tempfile
import yaml

from typing import Any
from typing import Optional
from rich.pretty import pprint
from click import get_current_context
from .environment import Environment

logger = logging.getLogger("Babylon")


class CommandResponse():
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
        return "\n".join([
            f"Command: {' '.join(self.command)}",
            "\n".join([f"  -  {key}: {param}" for key, param in self.params.items()]),
            f"Status code: {self.status_code}", "Return value:",
            str(self.data)
        ])

    def toJSON(self) -> str:
        return json.dumps(self.data, indent=4, ensure_ascii=False)

    def toYAML(self) -> str:
        return yaml.dump(self.data)

    def dump_yaml(self, output_file: pathlib.Path):
        """Dump command response data in a yaml file"""
        yaml_file = yaml.dump(self.data)
        tmpf = tempfile.NamedTemporaryFile(mode="w+")
        tmpf.write(yaml_file)
        tmpf.seek(0)
        shutil.copy(tmpf.name, output_file)
        tmpf.flush()
        tmpf.close()

    def dump_json(self, output_file: pathlib.Path):
        """Dump command response data in a json file"""
        with open(output_file, "w") as _f:
            _f.write(self.toJSON())
        logger.info(f"The JSON response was dumped in file: {output_file}")

    def has_failed(self) -> bool:
        """Checks if command has failed"""
        return self.status_code == self.STATUS_ERROR

    @classmethod
    def fail(cls, **kwargs) -> Any:
        return cls(status_code=CommandResponse.STATUS_ERROR, **kwargs)

    @classmethod
    def success(cls, data: Optional[dict[str, Any]] = None, **kwargs) -> Any:
        return cls(status_code=CommandResponse.STATUS_OK, data=data, **kwargs)
