"""Tests of GET /about."""

import pytest

from babylon_api.about import about


def test_about_endpoint(api, monkeypatch):
    monkeypatch.setenv("BABYLON_API_BUILD", "a6bdbc29")
    res = api.get("/about")
    assert res.status_code == 200
    version = res.json()["version"]
    assert version["build"] == "a6bdbc29"
    assert version["full"] == f"{version['release']}-a6bdbc29"


@pytest.mark.parametrize(
    "version, build, expected",
    [
        ("4.2.0", "a6bdbc29", {"full": "4.2.0-a6bdbc29", "release": "4.2.0", "major": 4, "minor": 2, "patch": 0, "label": ""}),
        ("5.5.4-rc1", "", {"full": "5.5.4-rc1", "release": "5.5.4-rc1", "major": 5, "minor": 5, "patch": 4, "label": "rc1"}),
        ("5.5.4", "", {"full": "5.5.4", "release": "5.5.4", "major": 5, "minor": 5, "patch": 4, "label": ""}),
        ("dev", "", {"full": "0.0.0-dev", "release": "0.0.0-dev", "major": 0, "minor": 0, "patch": 0, "label": "dev"}),
    ],
)
def test_about_parses_the_version(version, build, expected):
    result = about(version, {"BABYLON_API_BUILD": build}).version.model_dump()
    assert result == {**expected, "build": build}
