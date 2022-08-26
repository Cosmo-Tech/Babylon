import sys

import click

HELP_CONTEXT_OVERRIDE = {"help_option_names": ["-h", "--help"]}


def print_cmd_help(ctx, param, value):
    group = ctx.command
    # parse the cmdline and get the command and its arguments
    parser = group.make_parser(ctx)
    global_opts, args, _ = parser.parse_args(args=sys.argv[1:])
    if global_opts.get("help") is True or not args:
        # global help wanted
        click.echo(ctx.get_help())
        ctx.exit()

    # create the command object manually and parse its arguments
    cmd = group
    names = []
    prev_name = ""
    while args:
        try:
            name, cmd, args = cmd.resolve_command(ctx, args)
        except AttributeError:
            break
        if prev_name == name:
            break
        names.append(name)

    if set(args) & set(cmd.get_help_option_names(ctx)):
        # return command help when a user wants it or when he does not provide
        # arguments
        # taken from https://github.com/pallets/click/blob/7.1.1/src/click/core.py#L597
        cmd_ctx = click.Context(cmd, info_name=" ".join(names), parent=ctx)
        click.echo(cmd_ctx.get_help())
        cmd_ctx.exit()
