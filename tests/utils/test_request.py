from unittest.mock import patch, Mock
from Babylon.utils.request import oauth_request


@patch('requests.get')
def test_request_get(mocked_post: Mock):
    mocked_post.return_value = Mock(status_code=200, json=lambda: {"data": {"id": "test"}})
    response = oauth_request("", "")
    assert "data" in response.json()
    assert response.status_code == 200


@patch('requests.post')
def test_request_post(mocked_post: Mock):
    mocked_post.return_value = Mock(status_code=299, json=lambda: {"data": {"id": "test"}})
    response = oauth_request("", "", type="POST")
    assert "data" in response.json()
    assert response.status_code == 299


@patch('requests.get')
def test_request_fail(mocked_post: Mock):
    mocked_post.return_value = Mock(status_code=300, json=lambda: {"data": {"id": "test"}})
    response = oauth_request("", "")
    assert not response


def test_request_notype():
    response = oauth_request("", "", type="OUPS")
    assert not response
