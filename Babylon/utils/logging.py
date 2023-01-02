import logging
import os
from io import StringIO
from typing import Any
from typing import Optional

import rich.logging
from rich.console import Console
from rich.table import Table


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


def table_repr(table_content: list[dict[Any, Any]],
               title: Optional[str] = None,
               caption: Optional[str] = None) -> list[str]:
    """
    Take a list of dicts and will return a nice table representation
    :param table_content: list of dict to tabulate
    :param title: optional title for the table
    :param caption: optional caption for the table
    :return: list of strings for a pretty table display
    """

    pass
    """ The following code is commented, and replaced by a magic number for performances
    # Get handler, and use dummy message to compute prefix length from rich.logging
    _f = StringIO()
    _logger = logging.getLogger("Babylon")
    _handler: MultiLineHandler = next(_h for _h in _logger.handlers if isinstance(_h, MultiLineHandler))
    # levelname is "CRITICAL" because it is the longer standard log levelname
    _empty_record = logging.makeLogRecord({"msg": "", "levelname": "CRITICAL"})
    _message = _handler.format(_empty_record)
    _rendered_message = _handler.render_message(_empty_record, _message)
    _prefix = _handler.render(record=_empty_record, message_renderable=_rendered_message, traceback=None)
    _c = Console(file=_f)
    _c.print(_prefix)
    _f.seek(0)
    prefix = _f.read().rstrip()
    logging_prefix_size = len(prefix)
    """

    # Knowing prefix length display table with size dependent on terminal width
    _f = StringIO()
    # _c = Console(file=_f, width=os.get_terminal_size().columns - logging_prefix_size)
    _c = Console(file=_f, width=max(os.get_terminal_size().columns - 31, 20))
    _t = Table(title=title, caption=caption, show_edge=True)
    _keys = set()
    for _r in table_content:
        _keys.update(set(_r.keys()))
    for k in sorted(_keys):
        _t.add_column(header=k, justify="left", overflow="fold")
    for _r in table_content:
        _t.add_row(*(str(_r.get(_k)) for _k in sorted(_keys)))
    _c.print(_t)
    _f.seek(0)
    return list(_l.rstrip() for _l in _f.readlines())
