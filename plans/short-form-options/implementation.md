# Add -h Short-Form Help Option

## Goal
Enable `-h` as a short-form alias for `--help` across all Babylon commands by adding Click `context_settings` on the root CLI group.

## Prerequisites
Make sure you are on branch `feature/add-h-help-alias`. If the branch does not exist, create it from `main`.

### Step-by-Step Instructions

#### Step 1: Add global help alias and create tests
- [ ] Ensure you are on branch `feature/add-h-help-alias` (create it if necessary):

```bash
git checkout -b feature/add-h-help-alias
```

- [ ] Replace the contents of `Babylon/main.py` with the complete code block below (this adds `context_settings` to the root group so `-h` and `--help` are both available throughout the CLI):

```python
#!/usr/bin/env python3
import logging
import sys
from pathlib import Path as pathlibPath
from re import sub

import click_log
from click import Path as clickPath
from click import echo, group, option
from rich.logging import RichHandler

from Babylon.commands import list_groups
from Babylon.utils.decorators import prepend_doc_with_ascii
from Babylon.utils.dry_run import display_dry_run
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import INTERACTIVE_ARG_VALUE, interactive_run
from Babylon.version import VERSION

logger = logging.getLogger()
logging.getLogger("azure").setLevel(logging.WARNING)
u_log = logging.getLogger("urllib3")
k_log = logging.getLogger("kubernetes")

# On bloque la propagation vers le haut (le root logger qui affiche dans la console)
u_log.propagate = False
k_log.propagate = False
env = Environment()


class CleanFormatter(logging.Formatter):
    """Formatter that removes [color] tags for file logs."""

    def format(self, record):
        original_msg = record.msg
        if isinstance(record.msg, str):
            record.msg = sub(r"\[\/?[a-zA-Z0-9 #]+\]", "", record.msg)

        result = super().format(record)
        record.msg = original_msg
        return result


def print_version(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    echo(VERSION)
    ctx.exit()


def setup_logging(log_path: pathlibPath = pathlibPath.cwd()) -> None:
    import click  # noqa F401

    log_path.mkdir(parents=True, exist_ok=True)
    file_format = "%(asctime)s - %(levelname)s - %(name)s - %(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    file_formatter = CleanFormatter(fmt=file_format, datefmt=date_format)

    log_file_handler = logging.FileHandler(log_path / "babylon_info.log", encoding="utf-8")
    log_file_handler.setLevel(logging.INFO)
    log_file_handler.setFormatter(file_formatter)

    error_file_handler = logging.FileHandler(log_path / "babylon_error.log", encoding="utf-8")
    error_file_handler.setLevel(logging.WARNING)
    error_file_handler.setFormatter(file_formatter)
    logging.basicConfig(
        format="%(message)s",
        handlers=[
            log_file_handler,
            error_file_handler,
            RichHandler(
                show_time=False,
                rich_tracebacks=True,
                tracebacks_suppress=[click],
                omit_repeated_times=False,
                show_level=False,
                show_path=False,
                markup=True,
            ),
        ],
    )


@group(name="babylon", invoke_without_command=False, context_settings={'help_option_names': ['-h', '--help']})
@click_log.simple_verbosity_option(logger)
@option(
    "-n",
    "--dry-run",
    "dry_run",
    callback=display_dry_run,
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="Will run commands in dry-run mode.",
)
@option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Print version number and return.",
)
@option(
    "--log-path",
    "log_path",
    type=clickPath(file_okay=False, dir_okay=True, writable=True, path_type=pathlibPath),
    default=pathlibPath.cwd(),
    help="Path to the directory where log files will be stored. If not set, defaults to current working directory.",
)
@option(
    INTERACTIVE_ARG_VALUE,
    "interactive",
    is_flag=True,
    hidden=True,
    help="Start an interactive session after command run.",
)
@prepend_doc_with_ascii
def main(interactive, log_path):
    """
    CLI used for cloud interactions between CosmoTech and multiple cloud environment"""
    sys.tracebacklimit = 0
    setup_logging(pathlibPath(log_path))


main.result_callback()(interactive_run)

for _group in list_groups:
    main.add_command(_group)

if __name__ == "__main__":
    main()
```

- [ ] Create the test file `tests/unit/test_help_shortform.py` with the content below. This test uses Click's `CliRunner` and programmatically iterates the command hierarchy to verify that `-h` and `--help` both exit successfully and produce identical output.

```python
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
```

##### Step 1 Verification Checklist
- [ ] `git status` shows the intended changes staged before commit
- [ ] `python -m pytest tests/unit/test_help_shortform.py -q` exits with code 0 (run after manual verification step below)
- [ ] Spot-check several commands manually before running full tests:

```bash
# Manual spot checks (do these first):
python -m Babylon.main -h
python -m Babylon.main --help
python -m Babylon.main api -h
python -m Babylon.main api organizations get -h
```

#### Step 1 STOP & COMMIT
**STOP & COMMIT:** Stage and commit the changes now. Example:

```bash
git add Babylon/main.py tests/unit/test_help_shortform.py
git commit -m "Add -h alias for help via context_settings; add help shortform tests"
```

After committing, run the tests described above. If tests pass, proceed to update docs and open a PR.

