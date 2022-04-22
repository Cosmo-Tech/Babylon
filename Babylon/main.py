#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from clk.setup import basic_entry_point, main
from clk.decorators import command, argument, flag, option


@basic_entry_point(
    __name__,
    extra_command_packages=["Babylon.commands"],
    include_core_commands=["completion"],
)
def Babylon(**kwargs):
    pass


if __name__ == "__main__":
    main()
