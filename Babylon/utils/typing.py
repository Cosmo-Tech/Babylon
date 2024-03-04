import logging

from typing import Any
from typing import Optional
from click import Context
from click import ParamType
from click import Parameter
from .environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


class QueryType(ParamType):
    name = "QueryString"

    def convert(self, value: Any, param: Optional["Parameter"], ctx: Optional["Context"]) -> Any:
        """
        Convert the value of the parameter given in the console to the one passed to the underlying function
        :param value: the value sent by the console
        :param param: the name of the parameter
        :param ctx: the click context that lead to this call
        :return: the value of the parameter that should be sent to the function
        """

        logger.debug(f"Converting '{value}' for parameter '{param.name}'")
        try:
            print("convert str")
            r = ""
        except KeyError as _ke:
            self.fail(str(_ke), param, ctx)
        if r is None:
            return super().convert(value, param, ctx)

        logger.debug(f"   '{value}' -> '{r}'")
        return r
