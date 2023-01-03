import click

from Babylon.utils.response import CommandResponse


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
