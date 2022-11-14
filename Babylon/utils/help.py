import os
import sys

import click

HELP_CONTEXT_OVERRIDE = {"help_option_names": ["-h", "--help"]}


def print_cmd_help(ctx: click.Context, param: click.Parameter, value: str):
    if os.environ.get('BABYLON_RUNNING_TEST', False):
        return
    group = ctx.command
    # parse the cmdline and get the command and its arguments
    parser = group.make_parser(ctx)
    global_opts, args, _ = parser.parse_args(args=sys.argv[1:])
    if global_opts.get("help") is True or not args:
        # global help wanted
        click.echo(ctx.get_help())
        ctx.exit()

    # In case no help is found in the parameters we should not go further
    if not any(help_arg in args for help_arg in HELP_CONTEXT_OVERRIDE['help_option_names']):
        return

    # create the command object manually and parse its arguments
    cmd = group

    while args:
        name, cmd, args = cmd.resolve_command(ctx, args)
        ctx = click.Context(cmd, info_name=name, parent=ctx)
        cmd.parse_args(ctx, args)
