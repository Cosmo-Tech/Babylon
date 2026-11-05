"""Fetch the deployment files from a Git repository, safely.

The worker will call `prepare_checkout()` before running apply/destroy:
1. the host must be in an allow list (default: github.com),
2. only the requested ref is fetched, without history (fast, small),
3. a private-repo token never ends up on disk, in the URL or in the process list,
4. deploy_dir / variable files must really be inside the clone (symlinks included).
"""

from __future__ import annotations

import os
from re import sub, DOTALL
from base64 import b64encode
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from git import Git, GitCommandError

from Babylon.core.errors import BabylonError, InvalidOptionsError

ALLOWED_HOSTS_ENV = "BABYLON_API_ALLOWED_GIT_HOSTS"  # comma separated, e.g. "github.com,gitlab.cosmotech.com"
TOKEN_ENV = "BABYLON_API_GIT_TOKEN"  # optional, for private repositories
DEFAULT_ALLOWED_HOSTS = ("github.com",)
CLONE_TIMEOUT_SECONDS = 120


class RepositoryError(BabylonError):
    """The repository cannot be fetched (unreachable, unknown ref, bad credentials...)."""


@dataclass(frozen=True)
class Checkout:
    """A fetched repository and the resolved paths of the request."""

    root: Path
    commit: str  # exact sha deployed: "main" moves, the sha does not (traceability)
    deploy_dir: Path | None  # None for destroy (it works from the state only)
    variable_files: tuple[Path, ...]


def allowed_hosts(environ: dict | None = None) -> tuple[str, ...]:
    environ = os.environ if environ is None else environ
    raw = environ.get(ALLOWED_HOSTS_ENV, "")
    hosts = tuple(h.strip().lower() for h in raw.split(",") if h.strip())
    return hosts or DEFAULT_ALLOWED_HOSTS


def check_allowed_host(url: str, hosts: tuple[str, ...]) -> None:
    """Exact host match: 'github.com.evil.io' or 'evil.io/github.com' are refused."""
    host = (urlsplit(url).hostname or "").lower()
    if host not in hosts:
        raise InvalidOptionsError(f"Repository host '{host}' is not allowed. Allowed hosts: {', '.join(hosts)}")


def _git_env(token: str | None, allowed_protocols: str) -> dict:
    env = {
        "GIT_TERMINAL_PROMPT": "0",  # never wait for a password on stdin: fail instead
        "GIT_ALLOW_PROTOCOL": allowed_protocols,  # no ssh://, file://, ext:: ... even through redirects/submodules
        "GIT_CONFIG_NOSYSTEM": "1",  # ignore /etc/gitconfig of the image
    }
    if token:
        # Passed through environment-provided config (GIT_CONFIG_*): not in the URL, not in .git/config,
        # not visible in `ps` like a `-c` argument would be.
        basic = b64encode(f"x-access-token:{token}".encode()).decode()
        env.update(
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="http.extraHeader",
            GIT_CONFIG_VALUE_0=f"Authorization: Basic {basic}",
        )
    return env


def _error_message(exc: GitCommandError, token: str | None) -> str:
    """Last line of git stderr, token masked."""
    stderr = sub(r"^\s*stderr: '(.*)'\s*$", r"\1", str(exc.stderr or ""), flags=DOTALL).strip()
    message = stderr.splitlines()[-1] if stderr else f"exit code {exc.status}"
    return message.replace(token, "***") if token else message


def fetch_repository(url: str, ref: str, dest: Path, token: str | None = None, allowed_protocols: str = "https") -> str:
    """Fetch only `ref` (branch, tag or commit sha) of `url` into the empty directory `dest`. Returns the sha.

    `init + fetch --depth 1 <ref> + checkout FETCH_HEAD` instead of `clone --branch`:
    it also works with a commit sha, and downloads one commit only.
    `allowed_protocols` exists for tests (local "file" repositories); the API always uses https.
    """
    dest.mkdir(parents=True, exist_ok=True)
    git = Git(dest)
    git.update_environment(**_git_env(token, allowed_protocols))
    step = "init"
    try:
        git.init("--quiet")
        step = "fetch"
        # "--" ends the options: even a ref starting with "-" could not become a git option (already refused by the schema).
        # kill_after_timeout: a hanging server cannot block the worker until the Job deadline.
        git.fetch("--quiet", "--depth", "1", "--no-tags", "--", url, ref, kill_after_timeout=CLONE_TIMEOUT_SECONDS)
        step = "checkout"
        git.checkout("--quiet", "--detach", "FETCH_HEAD")
        step = "rev-parse"
        return git.rev_parse("HEAD")
    except GitCommandError as exc:
        raise RepositoryError(f"git {step} failed: {_error_message(exc, token)}") from None


def resolve_in_repo(root: Path, relative: str, *, expect_dir: bool) -> Path:
    """Path of `relative` inside `root`, refusing anything that escapes it (`..`, symlink to /etc...)."""
    root = root.resolve()
    path = (root / relative).resolve()  # follows symlinks: a link to /etc resolves to /etc
    if not path.is_relative_to(root):
        raise InvalidOptionsError(f"'{relative}' points outside the repository")
    if expect_dir and not path.is_dir():
        raise InvalidOptionsError(f"'{relative}' is not a directory of the repository")
    if not expect_dir and not path.is_file():
        raise InvalidOptionsError(f"'{relative}' is not a file of the repository")
    return path


def prepare_checkout(
    url: str,
    ref: str,
    dest: Path,
    deploy_dir: str | None,
    variable_files: list[str],
    environ: dict | None = None,
    allowed_protocols: str = "https",
) -> Checkout:
    """Host check -> fetch -> resolve paths. Raises InvalidOptionsError or RepositoryError."""
    environ = os.environ if environ is None else environ
    check_allowed_host(url, allowed_hosts(environ))
    commit = fetch_repository(url, ref, dest, token=environ.get(TOKEN_ENV) or None, allowed_protocols=allowed_protocols)
    return Checkout(
        root=dest,
        commit=commit,
        deploy_dir=resolve_in_repo(dest, deploy_dir, expect_dir=True) if deploy_dir is not None else None,
        variable_files=tuple(resolve_in_repo(dest, f, expect_dir=False) for f in variable_files),
    )
