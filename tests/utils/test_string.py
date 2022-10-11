from Babylon.utils.string import is_valid_command_name, to_header_line, MAX_LINE_LENGTH


def test_valid_command_wrong():
    """Testing string"""
    assert not is_valid_command_name("1wrong")


def test_valid_command_wrong_2():
    """Testing string"""
    assert not is_valid_command_name("wrong Command")


def test_valid_command_valid():
    """Testing string"""
    assert is_valid_command_name("rightCommand")


def test_valid_command_valid_2():
    """Testing string"""
    assert is_valid_command_name("right_command")


def test_header_line_empty():
    """Testing string"""
    assert to_header_line("") == "-" * MAX_LINE_LENGTH


def test_header_line_huge():
    """Testing string"""
    assert to_header_line("*"*(MAX_LINE_LENGTH+1)
                          ) == "*" * (MAX_LINE_LENGTH + 1)

def test_header_line_missing():
    """Testing string"""
    header = to_header_line("HEADER")
    assert "HEADER" in to_header_line("HEADER")
    idx = header.find("HEADER")
    # Check if centered
    assert idx == MAX_LINE_LENGTH / 2 - len("HEADER") // 2
