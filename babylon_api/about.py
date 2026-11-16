"""Version information of the running Babylon API (GET /about).

Same shape as the Cosmotech API /about:
    {"version": {"full": "5.5.4-a6bdbc29", "release": "5.5.4", "major": 5, "minor": 5, "patch": 4,
                 "label": "", "build": "a6bdbc29"}}
- release / major / minor / patch / label come from the package version (Babylon/version.py);
- build is the git sha baked into the image (Dockerfile ARG BUILD -> env BABYLON_API_BUILD).
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping

from pydantic import BaseModel

from Babylon.version import VERSION

BUILD_ENV = "BABYLON_API_BUILD"

# 5.5.4, 5.5.4-rc1, 5.5.4.dev2 ...: label = what follows major.minor.patch
_SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)[-.+]?(.*)$")


class Version(BaseModel):
    full: str
    release: str
    major: int
    minor: int
    patch: int
    label: str
    build: str


class About(BaseModel):
    version: Version


def about(version: str = VERSION, environ: Mapping[str, str] | None = None) -> About:
    environ = os.environ if environ is None else environ
    build = environ.get(BUILD_ENV, "").strip()
    match = _SEMVER.match(version)
    major, minor, patch, label = (int(match[1]), int(match[2]), int(match[3]), match[4]) if match else (0, 0, 0, version)
    release = f"{major}.{minor}.{patch}" + (f"-{label}" if label else "")
    return About(
        version=Version(
            full=f"{release}-{build}" if build else release,
            release=release,
            major=major,
            minor=minor,
            patch=patch,
            label=label,
            build=build,
        )
    )
