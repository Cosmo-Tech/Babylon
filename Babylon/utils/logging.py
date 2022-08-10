import logging


class MultiLineHandler(logging.StreamHandler):
    """
    Simple multiple line Handler for logging.
    Will separate multiline logs and emit them one line at a time
    """

    def __init__(self, *args, **kwargs):
        logging.StreamHandler.__init__(self, *args, **kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        base_msg = record.msg[:]
        for line in base_msg.split("\n"):
            record.msg = line
            logging.StreamHandler.emit(self, record)
