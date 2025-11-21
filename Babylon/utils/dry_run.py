import logging
import sys

import click
import rich
import rich.markdown

logger = logging.getLogger("Babylon")


def display_dry_run(ctx: click.Context, param: click.Parameter, value: str):
    group = ctx.command
    # parse the cmdline and get the command and its arguments
    parser = group.make_parser(ctx)
    global_opts, args, _ = parser.parse_args(args=sys.argv[1:])
    # create the command object manually and parse its arguments
    cmd = group

    is_dry_run = global_opts.get("dry_run", False)
    if not is_dry_run:
        return

    while args:
        name, cmd, args = cmd.resolve_command(ctx, args)
        ctx = click.Context(
            cmd,
            info_name=name,
            parent=ctx,
        )
        cmd.parse_args(ctx, args)

    r = [(ctx.command.name, ctx.params)]

    cmd_ctx = ctx
    while ctx.parent:
        ctx = ctx.parent
        r.append((ctx.command.name, ctx.params))
    console = rich.console.Console()
    console.print(" ".join(" ".join([c] + [f"--{k} {v}" for k, v in a.items()]) for c, a in r[::-1]))

    if "dry_run" in cmd_ctx.command.callback.__dict__:
        console.print(rich.markdown.Markdown(cmd_ctx.command.callback.dry_run))
    exit()
