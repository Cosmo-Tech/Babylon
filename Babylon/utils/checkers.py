import os
import re
import sys
import logging

from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


def check_alpha(value: str):
    if not str.isalpha(value):
        logger.error(f"'{value}' is invalid [alphabetic value only]")
        sys.exit(1)


def check_alphanum(value: str):
    if not str.isalnum(value):
        logger.error(f"'{value}' is invalid [alphanumeric value only]")
        sys.exit(1)


def check_ascii(value: str):
    if not str.isascii(value):
        logger.error(f"'{value}' is invalid [ascii value only]")
        sys.exit(1)


def check_exists(group: str, key: str, values: dict) -> dict:
    for i, k in values.items():
        if not str(k):
            logger.warning(f"You are trying to use the key {k}: '{key}' in group: '{group}'")
            logger.warning(f"Check {env.pwd}/{env.context_id}.{env.environ_id}.{group}.yaml file")
            sys.exit(1)
    return values


# Make a regular expression
# for validating an Email
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'


# for validating an Email
def check_email(email):
    # pass the regular expression
    # and the string into the fullmatch() method
    if not (re.fullmatch(regex, email)):
        logger.error("Invalid Email")
        sys.exit(1)


def check_encoding_key():
    if not os.environ.get("BABYLON_ENCODING_KEY"):
        logger.error("BABYLON_ENCODING_KEY is missing")
        sys.exit(1)
