from typing import IO

import mkdocs_gen_files
import requirements

_md_file: IO
with mkdocs_gen_files.open("dependencies.md", "w") as _md_file, open("requirements.txt") as _req:
    content = ["# List of dependencies", ""]

    _requirements: list[str] = _req.read().splitlines()

    for l in _requirements:
        if not l:
            content.append("")
        elif l[0] == "#":
            content.append(l[1:] + "  ")
        else:
            req = next(requirements.parse(l))
            _name = req.name
            content.append(f"[ ![PyPI - {_name}]"
                           f"(https://img.shields.io/pypi/l/{_name}?style=for-the-badge&labelColor=informational&label={_name})]"
                           f"(https://pypi.org/project/{_name}/)  ")

    _md_file.writelines(l + "\n" for l in content)
