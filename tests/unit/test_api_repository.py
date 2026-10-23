"""Tests of babylon_api.repository: real git, on local repositories (no network)."""

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from Babylon.core.errors import InvalidOptionsError
from babylon_api import repository
from babylon_api.app import app
from babylon_api.repository import (
    RepositoryError,
    allowed_hosts,
    check_allowed_host,
    fetch_repository,
    prepare_checkout,
    resolve_in_repo,
)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def origin(tmp_path: Path) -> dict:
    """A local repo with 2 commits on main and a tag v1 on the first one."""
    repo = tmp_path / "origin"
    (repo / "project").mkdir(parents=True)
    git(repo, "init", "--quiet", "--initial-branch", "main")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    (repo / "project" / "Organization.yaml").write_text("kind: Organization\n")
    (repo / "variables.yaml").write_text("v: 1\n")
    git(repo, "add", ".")
    git(repo, "commit", "--quiet", "-m", "first")
    git(repo, "tag", "v1")
    first = git(repo, "rev-parse", "HEAD")
    (repo / "variables.yaml").write_text("v: 2\n")
    git(repo, "commit", "--quiet", "-am", "second")
    return {"url": repo.as_uri(), "first": first, "head": git(repo, "rev-parse", "HEAD")}


def fetch(origin, ref, dest):
    return fetch_repository(origin["url"], ref, dest, allowed_protocols="file")


# allowed hosts


def test_default_and_configured_hosts():
    assert allowed_hosts({}) == ("github.com",)
    assert allowed_hosts({repository.ALLOWED_HOSTS_ENV: " GitHub.com, gitlab.acme.io ,"}) == ("github.com", "gitlab.acme.io")


@pytest.mark.parametrize(
    "url",
    ["https://github.com.evil.io/a/b", "https://evil.io/github.com/a", "https://user@evil.io/a", "https://gitlab.com/a/b"],
)
def test_host_must_match_exactly(url):
    with pytest.raises(InvalidOptionsError, match="not allowed"):
        check_allowed_host(url, ("github.com",))


def test_allowed_host_passes():
    check_allowed_host("https://GitHub.com/acme/deploy", ("github.com",))


# fetch


@pytest.mark.parametrize("ref_key, ref, expected_vars", [("head", "main", "v: 2"), ("first", "v1", "v: 1")])
def test_fetch_branch_and_tag(origin, tmp_path, ref_key, ref, expected_vars):
    sha = fetch(origin, ref, tmp_path / "co")
    assert sha == origin[ref_key]
    assert (tmp_path / "co" / "variables.yaml").read_text().strip() == expected_vars


def test_fetch_commit_sha_without_history(origin, tmp_path):
    sha = fetch(origin, origin["first"], tmp_path / "co")
    assert sha == origin["first"]
    assert git(tmp_path / "co", "rev-list", "--count", "HEAD") == "1"  # depth 1


def test_unknown_ref_is_a_repository_error(origin, tmp_path):
    with pytest.raises(RepositoryError, match="git fetch failed"):
        fetch(origin, "does-not-exist", tmp_path / "co")


def test_protocol_not_allowed_is_refused(origin, tmp_path):
    with pytest.raises(RepositoryError):
        fetch_repository(origin["url"], "main", tmp_path / "co")  # default: https only, file:// refused by git


def test_token_is_not_written_to_disk(origin, tmp_path):
    fetch_repository(origin["url"], "main", tmp_path / "co", token="s3cr3t-token", allowed_protocols="file")
    config = (tmp_path / "co" / ".git" / "config").read_text()
    assert "s3cr3t" not in config and "x-access-token" not in config


def test_token_is_masked_in_errors(tmp_path, monkeypatch):
    def failing_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 128, "", "fatal: could not read from https://s3cr3t@github.com")

    monkeypatch.setattr(repository.subprocess, "run", failing_run)
    with pytest.raises(RepositoryError) as exc:
        fetch_repository("https://github.com/a/b", "main", tmp_path / "co", token="s3cr3t")
    assert "s3cr3t" not in str(exc.value) and "***" in str(exc.value)


# paths inside the repository

def test_resolve_in_repo(tmp_path):
    (tmp_path / "project").mkdir()
    (tmp_path / "variables.yaml").write_text("")
    assert resolve_in_repo(tmp_path, "project", expect_dir=True) == (tmp_path / "project").resolve()
    with pytest.raises(InvalidOptionsError, match="not a directory"):
        resolve_in_repo(tmp_path, "missing", expect_dir=True)
    with pytest.raises(InvalidOptionsError, match="not a file"):
        resolve_in_repo(tmp_path, "project", expect_dir=False)


def test_symlink_escaping_the_repository_is_refused(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "project").symlink_to("/etc")  # a malicious repo can contain this
    (repo / "variables.yaml").symlink_to("/etc/hostname")
    with pytest.raises(InvalidOptionsError, match="outside the repository"):
        resolve_in_repo(repo, "project", expect_dir=True)
    with pytest.raises(InvalidOptionsError, match="outside the repository"):
        resolve_in_repo(repo, "variables.yaml", expect_dir=False)


# prepare_checkout: the whole sequence

@pytest.fixture
def local_fetch(origin, monkeypatch):
    """The request uses a github.com URL (host check), git really fetches the local origin."""
    real = repository.fetch_repository

    def fake(url, ref, dest, token=None, allowed_protocols="https"):
        return real(origin["url"], ref, dest, token=token, allowed_protocols="file")

    monkeypatch.setattr(repository, "fetch_repository", fake)


def test_prepare_checkout_for_apply(origin, tmp_path, local_fetch):
    co = prepare_checkout("https://github.com/acme/d", "main", tmp_path / "co", "project", ["variables.yaml"], environ={})
    assert co.commit == origin["head"]
    assert (co.deploy_dir / "Organization.yaml").exists()
    assert co.variable_files[0].read_text() == "v: 2\n"


def test_prepare_checkout_for_destroy_has_no_deploy_dir(tmp_path, local_fetch):
    co = prepare_checkout("https://github.com/acme/d", "main", tmp_path / "co", None, ["variables.yaml"], environ={})
    assert co.deploy_dir is None


def test_prepare_checkout_checks_host_before_fetching(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "fetch_repository", lambda *a, **k: pytest.fail("must not fetch"))
    with pytest.raises(InvalidOptionsError, match="not allowed"):
        prepare_checkout("https://gitlab.com/a/b", "main", tmp_path / "co", "project", ["v.yaml"], environ={})


def test_prepare_checkout_missing_deploy_dir(tmp_path, local_fetch):
    with pytest.raises(InvalidOptionsError, match="'nope' is not a directory"):
        prepare_checkout("https://github.com/acme/d", "main", tmp_path / "co", "nope", ["variables.yaml"], environ={})


# API

def test_api_refuses_a_host_not_allowed(monkeypatch):
    monkeypatch.setenv(repository.ALLOWED_HOSTS_ENV, "github.com")
    body = {"repository": {"url": "https://gitlab.com/a/b"}, "deploy_dir": "p", "context": "dev", "tenant": "dev"}
    res = TestClient(app).post("/apply", json=body)
    assert res.status_code == 422
    assert "not allowed" in res.json()["detail"]
