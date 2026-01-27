import pytest
from click.testing import CliRunner
from Babylon.main import main


def collect_paths(cmd, prefix=None):
    if prefix is None:
        prefix = []
    paths = [prefix]
    if getattr(cmd, "commands", None):
        for name, sub in cmd.commands.items():
            paths.extend(collect_paths(sub, prefix + [name]))
    return paths


def test_help_shortform_matches_longform():
    runner = CliRunner()
    paths = collect_paths(main)
    # dedupe
    seen = set()
    unique_paths = []
    for p in paths:
        key = tuple(p)
        if key in seen:
            continue
        seen.add(key)
        unique_paths.append(p)

    for path in unique_paths:
        short_args = path + ["-h"]
        long_args = path + ["--help"]
        res_short = runner.invoke(main, short_args)
        res_long = runner.invoke(main, long_args)
        assert res_short.exit_code == 0, (
            f"Command {' '.join(path) or 'main'} -h exited non-zero; exception: {res_short.exception}"
        )
        assert res_long.exit_code == 0, (
            f"Command {' '.join(path) or 'main'} --help exited non-zero; exception: {res_long.exception}"
        )
        assert res_short.output == res_long.output, (
            f"Help output mismatch for {' '.join(path) or 'main'}; -h vs --help"
        )
