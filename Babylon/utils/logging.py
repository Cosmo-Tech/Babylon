import logging
import rich.logging


class MultiLineHandler(rich.logging.RichHandler):
    """
    Simple multiple line Handler for logging.
    Will separate multiline logs and emit them one line at a time
    """

    def emit(self, record: logging.LogRecord) -> None:
        if not isinstance(record.msg, str):
            super().emit(record)
            return
        base_msg = record.msg[:]
        for line in base_msg.split("\n"):
            record.msg = line.rstrip()
            super().emit(record)
