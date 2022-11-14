import logging
import re
from typing import Any
from typing import List
from typing import Optional

import jmespath
from click import Context
from click import ParamType
from click import Parameter
from click.shell_completion import CompletionItem

from .environment import initialize_environment

logger = logging.getLogger("Babylon")
env = initialize_environment(logger)

WORKING_DIR_STRING = "workdir"
DEPLOY_STRING = "deploy"
PLATFORM_STRING = "platform"
PATH_SYMBOL = "%"


class QueryType(ParamType):
    name = "filetype"

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

        bases = [WORKING_DIR_STRING + '[]', DEPLOY_STRING, PLATFORM_STRING]
        base_names = [f"{PATH_SYMBOL}{base}{PATH_SYMBOL}" for base in bases]

        return [CompletionItem(_b) for _b in base_names if _b.startswith(incomplete)]

    @staticmethod
    def extract_value_content(value: Any) -> Optional[tuple[str, Optional[str], str]]:
        """
        Extract interesting information from a given value
        :param value: Value of the parameter to extract
        :return: None if value has no interesting info else element, filepath, and query
        """

        if not isinstance(value, str):
            return None

        check_regex = re.compile(f"{PATH_SYMBOL}"
                                 f"({PLATFORM_STRING}|{DEPLOY_STRING}|{WORKING_DIR_STRING})"
                                 f"(?:(?<={WORKING_DIR_STRING})\\[(.+)])?"
                                 f"{PATH_SYMBOL}"
                                 f"(.+)")

        # Regex groups captures :
        # 1 : Element to query : platform/deploy/workdir
        # 2 : File path to query in case of a working dir
        # 3 : jmespath query to apply

        match_content = check_regex.match(value)
        if not match_content:
            return None
        _type, _file, _query = match_content.groups()

        return _type, _file, _query

    def convert(self, value: Any, param: Optional["Parameter"], ctx: Optional["Context"]) -> Any:
        """
        Convert the value of the parameter given in the console to the one passed to the underlying function
        :param value: the value sent by the console
        :param param: the name of the parameter
        :param ctx: the click context that lead to this call
        :return: the value of the parameter that should be sent to the function
        """

        logger.debug(f"Converting '{value}' for parameter '{param.name}'")
        conf = env.configuration

        extracted_content = self.extract_value_content(value)
        if not extracted_content:
            logger.debug(f"  '{value}' -> no conversion applied")
            return super().convert(value, param, ctx)

        _type, _file, _query = extracted_content
        # Check content of platform / deploy
        possibles = {
            DEPLOY_STRING: (conf.get_deploy(), conf.get_deploy_path()),
            PLATFORM_STRING: (conf.get_platform(), conf.get_platform_path())
        }

        if _type in possibles:
            logger.debug(f"    Detected parameter type '{_type}' with query '{_query}'")
            _data, _path = possibles.get(_type)
            r = jmespath.search(_query, _data)
            if r is None:
                self.fail(f"Could not find results for query '{_query}' in {_path}", param, ctx)
        else:
            # Check content of workdir
            logger.debug(f"    Detected parameter type '{_type}' with query '{_query}' on file '{_file}'")
            wd = env.working_dir
            if not wd.requires_file(_file):
                self.fail(f"File '{_file}' does not exists in current working dir.", param, ctx)

            _content = wd.get_file_content(_file)
            r = jmespath.search(_query, _content)
            if r is None:
                self.fail(f"Could not find results for query '{_query}' in '{wd.get_file(_file)}'", param, ctx)

        logger.debug(f"   '{value}' -> '{r}'")
        return r
