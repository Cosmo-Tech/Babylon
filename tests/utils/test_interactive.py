from unittest.mock import patch

from Babylon.utils.interactive import ask_for_group, element_to_str, select_from_list


@patch("click.prompt", lambda x, type: "test")
def test_ask_for_group():
    """Testing interactive"""
    response = ask_for_group("test", exists=True)
    assert response == ["test"]


@patch("click.prompt", lambda x, type: "this  is a   group")
def test_ask_for_group_complex():
    """Testing interactive"""
    response = ask_for_group("test", exists=True)
    assert response == ["this", "is", "a", "group"]


@patch("click.prompt", lambda x, type: "")
def test_ask_for_group_empty():
    """Testing interactive"""
    response = ask_for_group("test", exists=True)
    assert response == []


def test1_element_to_str_unchecked():
    """Testing interactive"""
    assert element_to_str("a", "b") == "[ ] - a"


def test1_element_to_str_checked():
    """Testing interactive"""
    assert element_to_str("a", "a") == "[x] - a"


def test1_element_to_str_none():
    """Testing interactive"""
    assert element_to_str(None) == "None"


@patch("click.prompt", lambda x, type: 4)
def test_select_from_list_wrong():
    """Testing interactive"""
    select_from_list(["a", "b", "c", "d"])


@patch("click.prompt", lambda x, type: 1)
def test_select_from_list_good():
    """Testing interactive"""
    assert select_from_list(["a", "b", "c", "d"]) == "b"


@patch("click.prompt", lambda x, type: 1)
def test_select_from_list_none():
    """Testing interactive"""
    assert not select_from_list(None)
