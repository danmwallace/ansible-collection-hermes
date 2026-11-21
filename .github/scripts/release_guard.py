#!/usr/bin/env python3
"""Keep git tags, galaxy.yml and Ansible Galaxy in agreement.

Issue #41 found tags and Galaxy releases out of step for 1.2.x-1.3.x: tags
whose release run failed, tags pushed long after the fact that then published
old versions, and a release commit that carried stray local notes. Each
subcommand below closes one of those gaps:

  audit           (CI) every v* tag matches galaxy.yml at that commit, every
                  Galaxy version has a tag, and every tag is on Galaxy unless
                  .github/unpublished-tags.txt says why not.
  preflight       (release) decide whether a tag push should publish at all.
  check-tarball   (release) the built tarball holds only files tracked at the tag.
  verify-published (release) Galaxy serves the exact tarball that was built.

Stdlib only, so it runs before anything is pip-installed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

GALAXY = "https://galaxy.ansible.com"
VERSIONS = "/api/v3/plugin/ansible/content/published/collections/index/{ns}/{name}/versions/"
ALLOWLIST = Path(".github/unpublished-tags.txt")
# Local-only paths that must never ship, even if someone commits them by
# mistake (1.3.2 committed .superpowers/). Mirrors build_ignore in galaxy.yml.
DENY_TOP = {".ansible", ".claude", ".superpowers", ".venv", "dist"}
# Dot-paths that are tracked on purpose and fine to ship.
EXPECTED_DOT = {".github", ".gitignore"}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def field(text: str, name: str) -> str | None:
    """Top-level scalar from galaxy.yml; a regex avoids a PyYAML dependency."""
    m = re.search(rf"^{name}:\s*(.+?)\s*$", text, re.MULTILINE)
    return m.group(1).strip().strip("\"'") if m else None


def version_at(ref: str) -> str | None:
    try:
        return field(git("show", f"{ref}:galaxy.yml"), "version")
    except subprocess.CalledProcessError:
        return None


def key(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", version))


def fqcn() -> tuple[str, str]:
    text = Path("galaxy.yml").read_text()
    return field(text, "namespace"), field(text, "name")


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def galaxy_versions(ns: str, name: str) -> set[str]:
    found, path = set(), VERSIONS.format(ns=ns, name=name) + "?limit=100"
    while path:
        data = get_json(GALAXY + path)
        found.update(item["version"] for item in data.get("data", []))
        path = (data.get("links") or {}).get("next")
    return found


def galaxy_artifact(ns: str, name: str, version: str) -> dict | None:
    try:
        return get_json(f"{GALAXY}{VERSIONS.format(ns=ns, name=name)}{version}/")["artifact"]
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise


def allowlisted() -> dict[str, str]:
    """tag -> reason, from lines like `v1.3.2  # why it was never published`."""
    out = {}
    if ALLOWLIST.exists():
        for line in ALLOWLIST.read_text().splitlines():
            tag, _, reason = line.partition("#")
            if tag.strip():
                out[tag.strip()] = reason.strip()
    return out


def output(name: str, value: str) -> None:
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            fh.write(f"{name}={value}\n")


def cmd_audit(_: argparse.Namespace) -> int:
    ns, name = fqcn()
    published = galaxy_versions(ns, name)
    tags = {t[1:]: t for t in git("tag", "-l", "v*").split() if re.fullmatch(r"v\d+(\.\d+)*", t)}
    allowed = allowlisted()
    latest = max(published, key=key) if published else "0"
    errors = []

    for version, tag in sorted(tags.items(), key=lambda kv: key(kv[0])):
        at = version_at(f"{tag}^{{commit}}")
        if at != version:
            errors.append(f"{tag} points at a commit whose galaxy.yml says {at}")
        if version in published:
            if tag in allowed:
                errors.append(f"{tag} is on Galaxy; drop it from {ALLOWLIST}")
        elif tag in allowed:
            print(f"  -- {tag} not on Galaxy (allowed: {allowed[tag]})")
        elif key(version) > key(latest):
            # The release run for a just-pushed tag may still be going.
            print(f"::warning::{tag} is newer than Galaxy's latest ({latest}); release pending or failed?")
        else:
            errors.append(f"{tag} is not on Galaxy and not listed in {ALLOWLIST}")

    for version in sorted(published - tags.keys(), key=key):
        errors.append(f"Galaxy has {version} but there is no v{version} tag")
    for tag in sorted(allowed.keys() - {t for t in tags.values()}):
        errors.append(f"{ALLOWLIST} lists {tag}, which is not a tag")

    for err in errors:
        print(f"::error::{err}")
    print(f"{len(tags)} tags, {len(published)} Galaxy versions, {len(errors)} problems")
    return 1 if errors else 0


def cmd_preflight(args: argparse.Namespace) -> int:
    tag, version = args.tag, args.tag.removeprefix("v")
    at = version_at(f"{tag}^{{commit}}")
    if at != version:
        print(f"::error::tag {tag} does not match galaxy.yml version {at}")
        return 1

    commit = git("rev-parse", f"{tag}^{{commit}}")
    try:
        git("merge-base", "--is-ancestor", commit, "origin/main")
    except subprocess.CalledProcessError:
        print(f"::error::{tag} ({commit[:9]}) is not on main; release from main only")
        return 1

    ns, name = fqcn()
    published = galaxy_versions(ns, name)
    if version in published:
        print(f"::notice::{ns}.{name} {version} is already on Galaxy; nothing to publish")
        output("publish", "false")
        return 0

    latest = max(published, key=key) if published else None
    if latest and key(version) < key(latest) and not args.allow_backfill:
        # A tag added after the fact (to record history) must not quietly ship
        # an old version. On 2026-11-15, backfilled v1.3.0/v1.3.1 tags did.
        print(
            f"::error::{version} is older than Galaxy's latest ({latest}). If this tag "
            "only records history, add it to .github/unpublished-tags.txt. To really "
            "publish it, re-run this workflow by hand on the tag with allow_backfill."
        )
        return 1

    output("publish", "true")
    return 0


def cmd_check_tarball(args: argparse.Namespace) -> int:
    # path -> blob id at the tag; comparing blob ids also catches a tracked
    # file built from an uncommitted edit.
    tracked = {}
    for line in git("ls-tree", "-r", f"{args.tag}^{{commit}}").splitlines():
        meta, path = line.split("\t", 1)
        tracked[path] = meta.split()[2]
    errors, odd = [], set()
    with tarfile.open(args.tarball) as tar:
        for member in tar.getmembers():
            if not member.isfile() or member.name in {"MANIFEST.json", "FILES.json"}:
                continue
            top = member.name.split("/", 1)[0]
            data = tar.extractfile(member).read()
            blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
            if top in DENY_TOP:
                errors.append(f"local-only path in tarball: {member.name}")
            elif member.name not in tracked:
                errors.append(f"not tracked at {args.tag}: {member.name}")
            elif tracked[member.name] != blob:
                errors.append(f"differs from {args.tag}: {member.name}")
            elif top.startswith(".") and top not in EXPECTED_DOT:
                odd.add(top)
    for top in sorted(odd):
        print(f"::warning::tarball ships {top}/; add it to build_ignore if it is local-only")
    for err in errors:
        print(f"::error::{err}")
    return 1 if errors else 0


def cmd_verify_published(args: argparse.Namespace) -> int:
    ns, name = fqcn()
    version = args.tag.removeprefix("v")
    local = hashlib.sha256(Path(args.tarball).read_bytes()).hexdigest()
    for _ in range(10):
        artifact = galaxy_artifact(ns, name, version)
        if artifact:
            if artifact["sha256"] == local:
                print(f"Galaxy serves {artifact['filename']} sha256 {local}")
                return 0
            print(f"::error::Galaxy sha256 {artifact['sha256']} != built {local}")
            return 1
        time.sleep(15)
    print(f"::error::{ns}.{name} {version} did not appear on Galaxy")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("audit").set_defaults(func=cmd_audit)
    pre = sub.add_parser("preflight")
    pre.add_argument("--tag", required=True)
    pre.add_argument("--allow-backfill", action="store_true")
    pre.set_defaults(func=cmd_preflight)
    for cmd, func in (("check-tarball", cmd_check_tarball), ("verify-published", cmd_verify_published)):
        p = sub.add_parser(cmd)
        p.add_argument("--tag", required=True)
        p.add_argument("tarball")
        p.set_defaults(func=func)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
