"""Execute the eight-case protocol in PANEL_PROTOCOL.md using exact inputs."""

import gzip
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from sage.all import PolynomialRing

from generate_msolve_pilot import CURVE, FIELD, HERE, RING, X, eligible, semaev3


PROTOCOL = HERE / "PANEL_PROTOCOL.md"
OUTPUT = HERE / "panel"
GENERATOR_SHA256 = "29485f0283dc4c6e71c680f13e216a165e6775c4ec27817b47ff9edfb906c81c"
BASELINE_SHA256 = {
    "cayley": "b6fe3243bb257045fa55d24dc85835bda93d62c7e97ec9cc929ce08f66d7ae2a",
    "matched": "7dea3daf7feebcd5fefc0c4b026492a0a0f8b8544352d03d9958bd32258825b6",
}
TARGETS = [
    ("shared_ppp", (4660, 8866)),
    ("shared_mpp", (5131, 10178)),
    ("shared_pmp", (8142, 5977)),
    ("shared_ppm", (1996, 13869)),
    ("scalar_1", (1893, 12621)),
    ("scalar_137", (8541, 12965)),
    ("scalar_271", (10498, 13654)),
    ("scalar_997", (5370, 9573)),
]
ROUND = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+) x (\d+)\s", re.M)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def input_for(target_x, roots):
    ring = PolynomialRing(FIELD, names=("x1", "x2", "x3", "w"))
    x1, x2, x3, w = ring.gens()
    root_poly = RING.prod(X - FIELD(x) for x in roots)
    system = [
        semaev3(x1, x2, w),
        semaev3(w, x3, FIELD(target_x)),
        root_poly(x1),
        root_poly(x2),
        root_poly(x3),
    ]
    return ("x1,x2,x3,w\n15359\n" + ",\n".join(str(f) for f in system) + "\n").encode()


def main():
    assert PROTOCOL.exists()
    assert sha256((HERE / "generate_msolve_pilot.py").read_bytes()) == GENERATOR_SHA256
    fixture = json.loads((HERE / "pilot_fixture.json").read_text())
    assert fixture["curve_order"] == 15581 and CURVE.order().is_prime()
    points = [
        CURVE(FIELD(x), (FIELD(x) ** 3 + CURVE.a4() * FIELD(x) + CURVE.a6()).sqrt())
        for x in fixture["shared_roots"]
    ]
    for name, signs, xy in zip(
        ("shared_ppp", "shared_mpp", "shared_pmp", "shared_ppm"),
        ((1, 1, 1), (-1, 1, 1), (1, -1, 1), (1, 1, -1)),
        (xy for _, xy in TARGETS[:4]),
    ):
        target = sum((sign * point for sign, point in zip(signs, points)), CURVE(0))
        assert tuple(map(int, target.xy())) == xy, name
    generator = CURVE(FIELD(1893), FIELD(12621))
    assert generator.order() == CURVE.order()
    for (name, xy), scalar in zip(TARGETS[4:], (1, 137, 271, 997)):
        assert tuple(map(int, (scalar * generator).xy())) == xy, name

    OUTPUT.mkdir(exist_ok=True)
    records = []
    for name, xy in TARGETS:
        target = CURVE(FIELD(xy[0]), FIELD(xy[1]))
        assert tuple(map(int, target.xy())) == xy
        for arm in ("cayley", "matched"):
            contents = input_for(xy[0], fixture[f"{arm}_roots"])
            if name == "shared_ppp":
                assert sha256(contents) == BASELINE_SHA256[arm]
            stem = f"{name}_{arm}"
            ms_file = OUTPUT / f"{stem}.ms"
            out_file = OUTPUT / f"{stem}.out"
            log_file = OUTPUT / f"{stem}.log.gz"
            ms_file.write_bytes(contents)
            command = ["msolve", "-f", str(ms_file), "-o", str(out_file), "-v", "2"]
            started = time.perf_counter_ns()
            try:
                process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
                status = "exit"
                exit_code = process.returncode
                raw_log = process.stdout
            except subprocess.TimeoutExpired as error:
                status = "timeout"
                exit_code = None
                raw_log = error.stdout or b""
            wall_ns = time.perf_counter_ns() - started
            log_file.write_bytes(gzip.compress(raw_log, compresslevel=9, mtime=0))
            text = raw_log.decode(errors="replace")
            rounds = [tuple(map(int, match.groups())) for match in ROUND.finditer(text)]
            ideal_degrees = [int(x) for x in re.findall(r"^degree of ideal\s+(\d+)$", text, re.M)]
            output_text = out_file.read_text() if out_file.exists() else None
            record = {
                "case": name,
                "arm": arm,
                "target_xy": xy,
                "status": status,
                "exit_code": exit_code,
                "wall_ns": wall_ns,
                "input_sha256": sha256(contents),
                "log_sha256": sha256(raw_log),
                "output_sha256": sha256(output_text.encode()) if output_text is not None else None,
                "round_count": len(rounds),
                "round_geometry_sha256": sha256(json.dumps(rounds).encode()),
                "max_step_degree": max((row[0] for row in rounds), default=None),
                "ideal_degree": ideal_degrees[-1] if ideal_degrees else None,
                "has_solution": output_text is not None and not output_text.strip().startswith("[-1]"),
            }
            records.append(record)
            (OUTPUT / "summary.json").write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")
            print(json.dumps(record, sort_keys=True), flush=True)
    for name, _ in TARGETS[:4]:
        assert all(row["exit_code"] == 0 and row["has_solution"] for row in records if row["case"] == name)


if __name__ == "__main__":
    main()
