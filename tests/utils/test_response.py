import click
from unittest.mock import patch
from pathlib import PosixPath

from Babylon.utils.response import CommandResponse
from Babylon.utils.response import MacroReport


def test_response_empty():
    """Testing command responses"""
    ctx = click.Context(click.Command('cmd'))
    with ctx:
        CommandResponse.success()


def test_response_fail():
    """Testing command responses"""
    ctx = click.Context(click.Command('cmd'))
    with ctx:
        response = CommandResponse.fail()
        assert response.status_code == CommandResponse.STATUS_ERROR


def test_response_dict():
    """Testing command responses"""
    ctx = click.Context(click.Command('cmd'))
    with ctx:
        response = CommandResponse(status_code=CommandResponse.STATUS_OK, data={"oups": True})
        data = response.to_dict()
        assert data.get("status_code") == CommandResponse.STATUS_OK
        assert data.get("data") == {"oups": True}


def test_response_str():
    """Testing command responses"""
    ctx = click.Context(click.Command('cmd'))
    with ctx:
        response = CommandResponse(status_code=CommandResponse.STATUS_OK, data={"oups": True})
        assert "'oups'" in str(response)


def test_response_json():
    """Testing command responses"""
    ctx = click.Context(click.Command('cmd'))
    with ctx:
        response = CommandResponse.success({"oups": True})
        response.toJSON()


def test_report_ok():
    """Testing macro report"""
    report = MacroReport()
    ctx = click.Context(click.Command('cmd'))
    with ctx:
        report.addCommand("step 1", CommandResponse.success({"data": 1}))
    with patch("builtins.open") as file:
        report.dump("test.json")
        file.assert_called_with(PosixPath("test.json"), "w")


def test_report_duplicate():
    """Testing macro report"""
    report = MacroReport()
    ctx = click.Context(click.Command('cmd'))
    with ctx:
        report.addCommand("step 1", CommandResponse.success({"data": 1}))
    with patch("builtins.open") as file, patch("pathlib.Path.exists", lambda path: path == PosixPath("test.json")):
        report.dump("test.json")
        file.assert_called_with(PosixPath("test_1.json"), "w")
