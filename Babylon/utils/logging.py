import logging
from io import StringIO
from typing import Any, Optional

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
            record.msg = line
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
    _f = StringIO()
    _c = Console(file=_f, width=160)
    _t = Table(title=title, caption=caption, show_edge=True)
    _keys = set()
    for _r in table_content:
        _keys.update(set(_r.keys()))
    for k in sorted(_keys):
        _t.add_column(header=k, justify="full", overflow="fold")
    for _r in table_content:
        _t.add_row(*(str(_r.get(_k)) for _k in sorted(_keys)))
    _c.print(_t)
    _f.seek(0)
    return list(_l.rstrip() for _l in _f.readlines())
