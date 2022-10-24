from typing import TextIO

import mkdocs_gen_files
import requirements

_md_file: TextIO
with mkdocs_gen_files.open("dependencies.md", "w") as _md_file, open("requirements.txt") as _req:
    content = ["# List of dependencies", ""]

    _requirements: list[str] = _req.read().splitlines()

    for _l in _requirements:
        if not _l:
            content.append("")
        elif _l[0] == "#":
            content.append(_l[1:] + "  ")
        else:
            req = next(requirements.parse(_l))
            _name = req.name
            content.append(
                f"[ ![PyPI - {_name}]"
                f"(https://img.shields.io/pypi/l/{_name}?style=for-the-badge&labelColor=informational&label={_name})]"
                f"(https://pypi.org/project/{_name}/)  ")

    _md_file.writelines(_l + "\n" for _l in content)
