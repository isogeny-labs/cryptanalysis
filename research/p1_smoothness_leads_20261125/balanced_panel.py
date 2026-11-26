"""Execute the equal-decomposition arm in BALANCED_PROTOCOL.md."""

import gzip
import json
import re
import subprocess
import time

from generate_msolve_pilot import FIELD, HERE, eligible
from panel import ROUND, TARGETS, input_for, sha256
from validate_panel import count_decompositions


ROOTS = [248, 3977, 4499, 5118, 1869, 3300]
OUTPUT = HERE / "balanced"


def main():
    assert (HERE / "BALANCED_PROTOCOL.md").exists()
    assert len(ROOTS) == len(set(ROOTS)) == 6
    assert all(eligible(FIELD(x)) for x in ROOTS)
    old = json.loads((HERE / "panel" / "summary.json").read_text())
    reference = {row["case"]: row for row in old if row["arm"] == "cayley"}
    assert len(reference) == len(TARGETS) == 8
    expected = [6, 6, 6, 6, 0, 0, 0, 0]
    for (case, xy), count in zip(TARGETS, expected):
        assert count_decompositions(ROOTS, xy[0]) == count
        assert count_decompositions(
            json.loads((HERE / "pilot_fixture.json").read_text())["cayley_roots"], xy[0]
        ) == count
        assert reference[case]["input_sha256"] == sha256(
            (HERE / "panel" / f"{case}_cayley.ms").read_bytes()
        )

    OUTPUT.mkdir(exist_ok=True)
    records = []
    for case, xy in TARGETS:
        contents = input_for(xy[0], ROOTS)
        ms_file = OUTPUT / f"{case}.ms"
        out_file = OUTPUT / f"{case}.out"
        log_file = OUTPUT / f"{case}.log.gz"
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
        degrees = [int(x) for x in re.findall(r"^degree of ideal\s+(\d+)$", text, re.M)]
        output_text = out_file.read_text() if out_file.exists() else None
        record = {
            "case": case,
            "target_xy": xy,
            "exit_code": exit_code,
            "status": status,
            "wall_ns": wall_ns,
            "input_sha256": sha256(contents),
            "log_sha256": sha256(raw_log),
            "output_sha256": sha256(output_text.encode()) if output_text is not None else None,
            "round_count": len(rounds),
            "round_geometry_sha256": sha256(json.dumps(rounds).encode()),
            "max_step_degree": max((row[0] for row in rounds), default=None),
            "ideal_degree": degrees[-1] if degrees else None,
            "has_solution": output_text is not None and not output_text.strip().startswith("[-1]"),
            "reference_geometry_equal": sha256(json.dumps(rounds).encode()) == reference[case]["round_geometry_sha256"],
        }
        records.append(record)
        (OUTPUT / "summary.json").write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")
        print(json.dumps(record, sort_keys=True), flush=True)
    assert all(record["exit_code"] == 0 for record in records)
    assert all(record["has_solution"] == (index < 4) for index, record in enumerate(records))


if __name__ == "__main__":
    main()
