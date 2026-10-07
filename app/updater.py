"""
Self-updater for Car Code Reader.

Updates are published to a public GitHub repository:
    <repo>/release.json         {"version": "2.3", "notes": "...", "files": {"name.py": "<sha256>", ...}}
    <repo>/app/<name>           the files themselves
The app downloads newer files into a per-user folder, checks every file's SHA-256 against
release.json, and only then swaps the new set in. start.py loads that folder ahead of the
installed app, so nothing in /Applications ever changes and macOS never asks again.
"""

import hashlib
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request

from version import VERSION

# Filled in once the GitHub repository exists, as "owner/repo".
UPDATE_REPO = "HughWinstanley/car-code-reader"
BRANCH = "main"


def base_url():
    override = os.environ.get("CCR_UPDATE_URL")  # used for testing
    if override:
        return override.rstrip("/")
    if not UPDATE_REPO:
        return ""
    return f"https://raw.githubusercontent.com/{UPDATE_REPO}/{BRANCH}"


def updates_dir():
    if sys.platform == "darwin":
        root = os.path.expanduser("~/Library/Application Support/Car Code Reader")
    elif os.name == "nt":
        root = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Car Code Reader")
    else:
        root = os.path.expanduser("~/.car-code-reader")
    return os.path.join(root, "app")


def parse_version(text):
    return tuple(int(x) for x in re.findall(r"\d+", text or "0"))


def _fetch(url, timeout=15):
    """Download bytes. On a Mac, use the built-in curl first: it trusts the system's certificates,
    which a freshly installed python.org Python often doesn't."""
    if sys.platform == "darwin" and os.path.exists("/usr/bin/curl"):
        try:
            out = subprocess.run(["/usr/bin/curl", "-fsSL", "--max-time", str(timeout), url],
                                 capture_output=True, timeout=timeout + 5)
            if out.returncode == 0:
                return out.stdout
        except (OSError, subprocess.SubprocessError):
            pass
    ctx = ssl.create_default_context()
    try:
        import certifi  # noqa: F401  (present on many installs)
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    req = urllib.request.Request(url, headers={"User-Agent": f"CarCodeReader/{VERSION}",
                                               "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


def check():
    """-> release dict if a newer version is published, else None. Never raises."""
    base = base_url()
    if not base:
        return None
    try:
        rel = json.loads(_fetch(f"{base}/release.json").decode("utf-8"))
        if parse_version(rel.get("version")) > parse_version(VERSION) and rel.get("files"):
            return rel
    except Exception:  # noqa: BLE001 - offline, repo missing, bad JSON: just no update
        return None
    return None


def install(rel, progress=None):
    """Download every file, verify it, then swap the new set in. Raises on any problem,
    leaving the current version untouched."""
    base, target = base_url(), updates_dir()
    os.makedirs(os.path.dirname(target), exist_ok=True)
    staging = tempfile.mkdtemp(prefix="update-", dir=os.path.dirname(target))
    try:
        files = rel["files"]
        for i, (name, digest) in enumerate(sorted(files.items())):
            if "/" in name or "\\" in name or name.startswith("."):
                raise ValueError(f"Unexpected file name in the update: {name}")
            if progress:
                progress(i, len(files), name)
            data = _fetch(f"{base}/app/{name}", timeout=30)
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError(f"{name} didn't download correctly. Nothing was changed; try again later.")
            with open(os.path.join(staging, name), "wb") as f:
                f.write(data)
        with open(os.path.join(staging, "version.py"), "w", encoding="utf-8") as f:
            f.write(f'VERSION = "{rel["version"]}"\n')
        old = target + ".old"
        shutil.rmtree(old, ignore_errors=True)
        if os.path.isdir(target):
            os.replace(target, old)
        os.replace(staging, target)
        shutil.rmtree(old, ignore_errors=True)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def restart():
    """Start the app again from start.py (which picks up the new files) and end this copy."""
    if getattr(sys, "frozen", False):  # stand-alone Mac app: just start the app's own program again
        os.execv(sys.executable, [sys.executable])
    start = os.environ.get("CCR_START") or os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "start.py")
    if not os.path.exists(start):
        start = sys.argv[0]
    os.execv(sys.executable, [sys.executable, start])
