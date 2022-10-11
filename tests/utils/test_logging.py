import logging
import io
from Babylon.utils.logging import MultiLineHandler


def test_handler():
    """Testing logging"""
    logger = logging.getLogger("tests")
    stream = io.StringIO()
    logger.addHandler(MultiLineHandler(stream))
    logger.warning("A\nB\nC\n")
    assert stream.getvalue() == "A\nB\nC\n\n"

def test_handler_oneline():
    """Testing logging"""
    logger = logging.getLogger("tests")
    stream = io.StringIO()
    logger.addHandler(MultiLineHandler(stream))
    logger.warning("A")
    assert stream.getvalue() == "A\n"