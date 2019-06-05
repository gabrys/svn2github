#!/usr/bin/env python3

import subprocess as proc
from subprocess import DEVNULL, PIPE, Popen
import re
from collections import namedtuple
import os
import tempfile
import shutil
import sys
import argparse


class Svn2GithubException(Exception):
    pass


GitSvnInfo = namedtuple('GitSvnInfo', 'svn_url svn_revision svn_uuid')


def get_last_revision_from_svn(svn_url):
    result = proc.run(["svn", "info", svn_url, "--no-newline", "--show-item", "revision"], check=True, stderr=DEVNULL, stdin=DEVNULL, stdout=PIPE)

    rev = int (result.stdout.decode().strip())
    if rev:
        return rev

    return Svn2GithubException("svn info {} output did not specify the current revision".format(svn_url))


def run_git_cmd(args, git_dir):
    return proc.run(["git"] + args, check=True, cwd=git_dir, stderr=DEVNULL, stdin=DEVNULL, stdout=PIPE)


def is_repo_empty(git_dir):
    result = proc.run(["ls", ".git/refs/heads"], check=True, cwd=git_dir, stderr=DEVNULL, stdin=DEVNULL, stdout=PIPE)
    return len(result.stdout) == 0


def get_svn_info_from_git(git_dir):
    result = run_git_cmd(["log", "-1", "HEAD", "--pretty=%b"], git_dir=git_dir)

    pattern = re.compile("^git-svn-id: (.*)@([0-9]+) ([0-9a-f-]{36})$".encode())

    for line in result.stdout.split("\n".encode()):
        m = pattern.match(line)
        if m:
             return GitSvnInfo(svn_url=m.group(1), svn_revision=int(m.group(2)), svn_uuid=m.group(3))

    return Svn2GithubException("git log -1 HEAD --pretty=%b output did not specify the current revision")


def git_svn_init(git_svn_info, git_dir):
    if git_svn_info.svn_uuid:
        rewrite_uuid = ["--rewrite-uuid", git_svn_info.svn_uuid]
    else:
        rewrite_uuid = []
    run_git_cmd(["svn", "init"] + rewrite_uuid + [git_svn_info.svn_url], git_dir)


def git_svn_rebase(git_dir):
    run_git_cmd(["svn", "rebase"], git_dir)


def git_svn_fetch(git_dir):
    cmd = Popen(["git", "svn", "fetch"], cwd=git_dir, stdin=DEVNULL, stdout=PIPE, stderr=DEVNULL, universal_newlines=True)

    pattern = re.compile("^r([0-9]+) = [0-9a-f]{40}")

    while True:
        line = cmd.stdout.readline()
        if not line:
            break
        m = pattern.match(line)
        if m:
            yield int(m.group(1))


def git_clone(git_src, git_dir):
    os.makedirs(git_dir, exist_ok=False)
    run_git_cmd(["clone", git_src, "."], git_dir)


def git_push(git_dir):
    run_git_cmd(["push", "origin", "master"], git_dir)


def unpack_cache(cache_path, git_dir):
    dot_git_dir = os.path.join(git_dir, ".git")
    os.makedirs(dot_git_dir, exist_ok=False)
    proc.run(["tar", "-xf", cache_path], check=True, cwd=dot_git_dir, stderr=DEVNULL, stdin=DEVNULL, stdout=DEVNULL)
    run_git_cmd(["config", "core.bare", "false"], git_dir)
    run_git_cmd(["checkout", "."], git_dir)


def save_cache(cache_path, tmp_path, git_dir):
    dot_git_dir = os.path.join(git_dir, ".git")
    proc.run(["tar", "-cf", tmp_path, "."], check=True, cwd=dot_git_dir, stderr=DEVNULL, stdin=DEVNULL, stdout=DEVNULL)
    shutil.copyfile(tmp_path, cache_path)


def sync_github_mirror(github_repo, cache_dir, new_svn_url=None):
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, "cache." + github_repo.replace("/", ".") + ".tar")
        cached = os.path.exists(cache_path)
    else:
        cached = False

    github_url = "git@github.com:" + github_repo + ".git"

    with tempfile.TemporaryDirectory(prefix="svn2github-") as tmp_dir:
        git_dir = os.path.join(tmp_dir, "repo")
        if cached and not new_svn_url:
            print("Using cached Git repository from " + cache_path)
            unpack_cache(cache_path, git_dir)
        else:
            print("Cloning " + github_url)
            git_clone(github_url, git_dir)

        if new_svn_url:
            if not is_repo_empty(git_dir):
                raise Svn2GithubException("Specifed new_svn_url, but the destination repo is not empty")
            git_svn_info = GitSvnInfo(svn_url=new_svn_url, svn_revision=0, svn_uuid=None)
        else:
            git_svn_info = get_svn_info_from_git(git_dir)

        print("Checking for SVN updates")
        upstream_revision = get_last_revision_from_svn(git_svn_info.svn_url)

        print("Last upstream revision: " + str(upstream_revision))
        print("Last mirrored revision: " + str(git_svn_info.svn_revision))
        if upstream_revision == git_svn_info.svn_revision:
            print("Everything up to date. Bye!")
            return

        print("Fetching from SVN", end="")
        if not cached or new_svn_url:
            git_svn_init(git_svn_info, git_dir)

        for rev in git_svn_fetch(git_dir):
            print("\rFetching from SVN, revision {}/{}".format(rev, upstream_revision), end="")
        print()

        print("Rebasing SVN changes")
        git_svn_rebase(git_dir)

        print("Pushing to GitHub")
        git_push(git_dir)

        if cache_dir:
            print("Saving Git directory to cache")
            save_cache(cache_path, os.path.join(tmp_dir, "cache.tar"), git_dir)


def main():
    parser = argparse.ArgumentParser(description="Mirror SVN repositories to GitHub")
    parser.add_argument("--cache-dir", help="Directory to keep the cached data to avoid re-downloading all SVN and Git history each time. This is optional, but highly recommended")
    subparsers = parser.add_subparsers()

    subparser_import = subparsers.add_parser("import", help="Import SVN repository to the GitHub repo")
    subparser_import.add_argument("github_repo", metavar="GITHUB_REPO", help="GitHub repo in format: user/name")
    subparser_import.add_argument("svn_url", metavar="SVN_URL", help="SVN repository to import")

    subparser_update = subparsers.add_parser("update", help="Update the GitHub repository from SVN")
    subparser_update.add_argument("github_repo", metavar="GITHUB_REPO", help="GitHub repo in format: user/name")
    args = parser.parse_args(sys.argv[1:] or ["--help"])

    new_svn_url = args.svn_url if "svn_url" in args else None
    sync_github_mirror(args.github_repo, args.cache_dir, new_svn_url=new_svn_url)



if __name__ == "__main__":
    main()
