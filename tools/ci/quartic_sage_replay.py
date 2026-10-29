#!/usr/bin/env python3
"""Replay original Sage workers in their unchanged, disposable recorded layout."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from check_quartic_certificates import MANIFEST, REPOSITORY, verify_inputs
from quartic_portable_replay import copy_verified, new_output

RESOLVENT = "experiments/hecke-432-j1728-resolvent-field-20261026"
SQRT2 = "experiments/hecke-432-j1728-sqrt2-split-20261026"
MODES = {
    "resolvent-producer": (RESOLVENT, "field_factor_sage.py",
                           ("coordinate_field.json", "factor_certificate.json", "field_factor_result.json")),
    "resolvent-check": (RESOLVENT, "check_certificate_sage.py", ("certificate_check.json",)),
    "sqrt2-producer": (SQRT2, "export_sqrt2_sage.py", ("sqrt2_factor_certificate.json",)),
    "sqrt2-check": (SQRT2, "check_certificate_sage.py", ("certificate_check.json",)),
}


def positive_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError("timeout must be a finite positive number")
    return number


def checked_command(sage_root, script, repository=REPOSITORY):
    if not Path(sage_root).is_absolute():
        raise ValueError("--sage-root must be an absolute in-image Sage checkout path")
    return [sys.executable, str(repository / "scripts/sage_release.py"), "run",
            "--sage", str(sage_root), "--", "-python", str(script)]


def prepare(source, destination, manifest, mode):
    """Never change path strings, protocols, certificate hashes or original bytes."""
    copy_verified(source, destination, manifest["inputs"])
    study, worker, outputs = MODES[mode]
    script = Path(destination) / study / worker
    if str(Path(study) / worker) not in manifest["inputs"]:
        raise ValueError("worker is not a pinned frozen input")
    for name in outputs:
        (script.parent / name).unlink(missing_ok=True)
    return script


def execute(command, directory, output, generated, timeout):
    """Record failure and timeouts; a fresh receipt cannot inherit old success."""
    timeout = positive_seconds(timeout)
    start = time.monotonic()
    with (output / "stdout.txt").open("w") as stdout, (output / "stderr.txt").open("w") as stderr:
        worker = subprocess.Popen(command, cwd=directory, stdout=stdout, stderr=stderr,
                                  start_new_session=True)
        try:
            code = worker.wait(timeout=timeout)
            status = "COMPLETED" if code == 0 else "CHECKED_SAGE_OR_WORKER_ERROR"
        except subprocess.TimeoutExpired:
            try:
                os.killpg(worker.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            worker.wait()
            code, status = 124, "TIME_LIMIT"
    hashes = {}
    for name in generated:
        path = directory / name
        if path.is_file():
            hashes[name] = sha256(path.read_bytes()).hexdigest()
            # Export only known worker outputs, never the writable source copy.
            (output / name).write_bytes(path.read_bytes())
    if code == 0 and len(hashes) != len(generated):
        code, status = 1, "MISSING_OUTPUT"
    return {"status": status, "returncode": code, "outputs": hashes,
            "elapsed_seconds": round(time.monotonic() - start, 3)}


def docker_command(image, sage_root, mode, timeout, output):
    if not re.fullmatch(r"[^\s]+@sha256:[0-9a-f]{64}", image):
        raise ValueError("--image must be pinned by its full sha256 digest")
    checked_command(sage_root, Path("/worker"))
    positive_seconds(timeout)
    return ["docker", "run", "--rm", "--network=none", "--read-only", "--user", "0:0",
            "--cap-drop=ALL", "--security-opt=no-new-privileges",
            "--tmpfs", "/Volumes:rw,nosuid,nodev,size=1g,mode=1777",
            "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m,mode=1777",
            "--env", "DOT_SAGE=/tmp/sage-home",
            "--mount", f"type=bind,src={REPOSITORY},dst=/source,readonly",
            "--mount", f"type=bind,src={output},dst=/evidence",
            "--entrypoint", "python3", image,
            "/source/tools/ci/quartic_sage_replay.py", mode,
            "--sage-root", str(sage_root), "--timeout-seconds", str(timeout),
            "--inside-container"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=MODES)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--image", help="image@sha256:digest containing the accepted optimized Sage checkout")
    parser.add_argument("--sage-root", required=True, help="absolute path to that Sage checkout inside the image")
    parser.add_argument("--timeout-seconds", required=True, type=positive_seconds,
                        help="explicit correctness-replay cap; these protocols declare no execution timeout")
    parser.add_argument("--inside-container", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    manifest = json.loads(MANIFEST.read_text())
    if verify_inputs(REPOSITORY, manifest["inputs"]):
        raise ValueError("frozen source mismatch")
    if args.inside_container:
        if REPOSITORY != Path("/source") or not Path("/.dockerenv").exists():
            raise ValueError("internal mode requires the disposable container")
        output = Path("/evidence")
        script = prepare(REPOSITORY, Path(manifest["original_root"]), manifest, args.mode)
        command = checked_command(args.sage_root, script)
        metadata = {"mode": args.mode, "command": command, "timeout_seconds": args.timeout_seconds,
                    "source_sha256": sha256(script.read_bytes()).hexdigest(),
                    "protocol_sha256": sha256((script.parent / "protocol.json").read_bytes()).hexdigest(),
                    "manifest_sha256": sha256(MANIFEST.read_bytes()).hexdigest()}
        metadata.update(execute(command, script.parent, output, MODES[args.mode][2], args.timeout_seconds))
        (output / "attempt.json").write_text(json.dumps(metadata, indent=2) + "\n")
        return metadata["returncode"]
    if args.out is None or args.image is None:
        parser.error("--out and --image are required")
    if args.out.resolve().is_relative_to(REPOSITORY):
        raise ValueError("output must be outside the source checkout")
    # Validate arguments before creating any output directory.
    docker_command(args.image, args.sage_root, args.mode, args.timeout_seconds, args.out)
    output = new_output(args.out)
    command = docker_command(args.image, args.sage_root, args.mode, args.timeout_seconds, output)
    (output / "launch.json").write_text(json.dumps({"command": command, "image": args.image}, indent=2) + "\n")
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
