#!/usr/bin/env python3
"""Replay frozen integer audits in their recorded layout in a disposable container."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from check_quartic_certificates import MANIFEST, REPOSITORY, verify_inputs

RUNTIME = REPOSITORY / "tools/ci/quartic-runtime"


def build_runtime():
    digest = sha256(b"".join((RUNTIME / name).read_bytes()
                              for name in ("Dockerfile", "requirements.txt"))).hexdigest()
    image = "quartic-certificate-replay:" + digest[:24]
    command = ["docker", "build", "--tag", image]
    if os.environ.get("CODEX_PROXY_CERT"):
        command += ["--secret", "id=proxy_ca,src=" + os.environ["CODEX_PROXY_CERT"]]
    subprocess.run(command + [str(RUNTIME)], check=True)
    return image


def copy_verified(source, destination, expected):
    """Create a new copy only after checking every original input."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination == source or destination.is_relative_to(source):
        raise ValueError("the replay copy must be outside the source checkout")
    failures = verify_inputs(source, expected)
    if failures:
        raise ValueError(f"frozen input mismatch: {failures[:3]}")
    destination.mkdir(parents=True, exist_ok=False)
    for name in expected:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    if verify_inputs(destination, expected):
        raise ValueError("copied input mismatch")


def new_output(path, source=REPOSITORY):
    path, source = Path(path).absolute(), Path(source).resolve()
    if path.resolve().is_relative_to(source / "experiments"):
        raise ValueError("outputs must be outside the frozen experiments tree")
    path.mkdir(parents=True, exist_ok=False)
    return path.resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--inside-container", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    manifest = json.loads(MANIFEST.read_text())
    if args.inside_container:
        original = Path(manifest["original_root"])
        copy_verified(REPOSITORY, original, manifest["inputs"])
        return subprocess.call([
            sys.executable, str(REPOSITORY / "tools/ci/check_quartic_certificates.py"),
            "integer", "--root", str(original), "--evidence", "/evidence",
        ])
    if args.out is None:
        parser.error("--out must name a new directory")
    failures = verify_inputs(REPOSITORY, manifest["inputs"])
    if failures:
        raise ValueError(f"frozen input mismatch: {failures[:3]}")
    image = build_runtime()
    output = new_output(args.out)
    command = [
        "docker", "run", "--rm", "--network=none", "--read-only",
        "--tmpfs", "/Volumes:rw,nosuid,nodev,size=1g",
        "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
        "--mount", f"type=bind,src={REPOSITORY},dst=/source,readonly",
        "--mount", f"type=bind,src={output},dst=/evidence",
        image, "python", "/source/tools/ci/quartic_portable_replay.py", "--inside-container",
    ]
    (output / "launch.json").write_text(json.dumps({"command": command, "image": image}, indent=2) + "\n")
    code = subprocess.call(command)
    if verify_inputs(REPOSITORY, manifest["inputs"]):
        raise ValueError("source bytes changed during replay")
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
