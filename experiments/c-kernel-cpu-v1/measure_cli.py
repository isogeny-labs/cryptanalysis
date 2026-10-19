#!/usr/bin/env python3
"""Record and validate an ECC2K CLI command for the Tier 0 service."""
import argparse
import json
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundary", choices=("process", "internal", "native"), required=True)
    parser.add_argument("--result-field", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide the child command after --")

    before = time.monotonic_ns()
    try:
        child = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        print(json.dumps({"status": "launch_failed", "verified": 0, "error": str(exc)}))
        return 1
    outer_ms = (time.monotonic_ns() - before) / 1_000_000
    lines = child.stdout.splitlines()
    final = None
    for line in reversed(lines):
        try:
            final = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    valid = child.returncode == 0 and isinstance(final, dict) and final.get("status") == "ok"
    if isinstance(final, dict) and final.get("badReports", 0) != 0:
        valid = False
    if not valid or args.result_field not in final:
        result = {
            "status": "invalid",
            "verified": 0,
            "returncode": child.returncode,
            "outer_ms": outer_ms,
            "stdout": child.stdout,
            "stderr": child.stderr,
            "child": final,
        }
        print(json.dumps(result, sort_keys=True))
        return 1
    if args.boundary == "internal":
        if not isinstance(final.get("seconds"), (int, float)) or final["seconds"] <= 0:
            print(json.dumps({"status": "invalid", "verified": 0, "reason": "missing positive internal seconds", "child": final}))
            return 1
        online_ms = float(final["seconds"]) * 1000
    elif args.boundary == "native":
        if not isinstance(final.get("online_ms"), (int, float)) or final["online_ms"] <= 0:
            print(json.dumps({"status": "invalid", "verified": 0, "reason": "missing positive native online_ms", "child": final}))
            return 1
        online_ms = float(final["online_ms"])
    else:
        online_ms = outer_ms
    print(json.dumps({
        "status": "ok",
        "verified": 1,
        "online_ms": online_ms,
        "outer_ms": outer_ms,
        "result": str(final[args.result_field]),
        "child": final,
        "stdout": child.stdout,
        "stderr": child.stderr,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
