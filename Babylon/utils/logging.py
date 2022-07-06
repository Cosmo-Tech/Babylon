import logging


class MultiLineHandler(logging.StreamHandler):

    def __init__(self, *args, **kwargs):
        logging.StreamHandler.__init__(self, *args, **kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        base_msg = record.msg[:]
        for line in base_msg.split("\n"):
            record.msg = line
            logging.StreamHandler.emit(self, record)
