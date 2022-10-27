import logging
import rich.logging


class MultiLineHandler(rich.logging.RichHandler):
    """
    Simple multiple line Handler for logging.
    Will separate multiline logs and emit them one line at a time
    """

    def emit(self, record: logging.LogRecord) -> None:
        base_msg = record.msg[:]
        for line in base_msg.split("\n"):
            record.msg = line
            super().emit(record)
