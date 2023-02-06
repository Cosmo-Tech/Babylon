import logging
from typing import Any
from typing import List
from typing import Optional

from click import Context
from click import ParamType
from click import Parameter
from click.shell_completion import CompletionItem

from .environment import Environment
from .environment import PATH_SYMBOL

logger = logging.getLogger("Babylon")
env = Environment()


class QueryType(ParamType):
    name = "QueryString"

    def shell_complete(self, ctx: "Context", param: "Parameter", incomplete: str) -> List["CompletionItem"]:
        """
        Allow auto-completion of the parameter
        :param ctx: click context used to send this parameter value
        :param param: name of the parameter to be completed
        :param incomplete: actual value to complete
        :return: a list of item that could be the completed version of the parameter
        """
        if not incomplete.startswith(PATH_SYMBOL):
            return []

        base_names = env.auto_completion_guide()

        return [CompletionItem(_b) for _b in base_names if _b.startswith(incomplete)]

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
            r = env.convert_data_query(query=value)
        except KeyError as _ke:
            self.fail(str(_ke), param, ctx)
        if r is None:
            return super().convert(value, param, ctx)

        logger.debug(f"   '{value}' -> '{r}'")
        return r
