"""Frozen source-mask prefix families in the exact N41 four-pair public XCNF."""

import hashlib
import itertools
import json
import random
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_allseed_fourpair_20261012"
sys.path.insert(0, str(SOURCE))
import fourpair_v2  # noqa: E402

SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
XCNF = SOURCE / "v2_n41_control.xcnf"
FIXTURE = SOURCE / "n41_diagonal/control_fixture.json"
BUILD = SOURCE / "v2_n41_control.json"
FLAGS = ("--threads=1", "--maxtime=8", "--zero-exit-status", "--verb=1", "--printsol=1")
CASE_CAP_NS = 10_000_000_000
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def inputs():
    fixture = json.loads(FIXTURE.read_text())
    build = json.loads(BUILD.read_text())
    assert sha(XCNF) == build["formula_sha256"]
    circuit, wires, meta = fourpair_v2.build("n41", fixture["target_reciprocal"])
    assert circuit.next_var - 1 == build["variables"]
    assert len(circuit.clauses) == build["clauses"]
    assert len(circuit.xors) == build["xor_rows"]
    support = fourpair_v2.support("n41")
    masks = [m for pair in fixture["masks"] for m in pair]
    assert len(masks) == 8 and all(m in support for m in masks)
    return fixture, build, wires, support, masks


def matching(domains, support):
    """Check an injective folded-column choice before giving a family to SAT."""
    columns = [set(support[m] for m in domain) for domain in domains]
    chosen = {}

    def augment(slot, seen):
        for col in sorted(columns[slot]):
            if col in seen:
                continue
            seen.add(col)
            if col not in chosen or augment(chosen[col], seen):
                chosen[col] = slot
                return True
        return False

    return all(augment(slot, set()) for slot in range(8))


def family(depth, prefixes, support):
    return [sorted(m for m in support if (m >> (8 - depth)) == prefix)
            for prefix in prefixes]


def prepare():
    fixture, build, wires, support, masks = inputs()
    rng = random.Random(20261012)
    panel = []
    for depth in (2, 3, 4):
        positive = [mask >> (8 - depth) for mask in masks]
        panel.append((f"d{depth}_positive", depth, positive, True))
        allowed = [p for p in range(1 << depth)
                   if len(family(depth, [p], support)[0]) >= 2]
        seen = {tuple(positive)}
        while len([x for x in panel if x[1] == depth]) < 4:
            prefixes = tuple(rng.choice(allowed) for _ in range(8))
            if prefixes in seen:
                continue
            domains = family(depth, prefixes, support)
            if not matching(domains, support):
                continue
            seen.add(prefixes)
            panel.append((f"d{depth}_random{len(seen)-1}", depth, prefixes, False))
    panel.append(("full_positive", 8, masks, True))
    rows = []
    head = XCNF.read_text().splitlines(keepends=True)
    assert head[0] == "p cnf 14803 38696\n"
    for label, depth, prefixes, is_positive in panel:
        domains = family(depth, prefixes, support)
        assert all(domains) and matching(domains, support)
        units = []
        for slot, prefix in enumerate(prefixes):
            for bit in range(8 - depth, 8):
                wire = wires["masks"][slot][bit]
                units.append(wire if (prefix >> (bit - (8 - depth))) & 1 else -wire)
        # Prefixes are the high bits of the original integer mask.
        for slot, prefix in enumerate(prefixes):
            assert all((mask >> (8 - depth)) == prefix for mask in domains[slot])
            if is_positive:
                assert masks[slot] in domains[slot]
        path = HERE / f"{label}.xcnf"
        with path.open("x") as out:
            out.write(f"p cnf 14803 {38696 + len(units)}\n")
            out.writelines(head[1:])
            out.writelines(f"{lit} 0\n" for lit in units)
        rows.append({"label": label, "depth": depth, "prefixes": list(prefixes),
                     "positive_control": is_positive, "domain_sizes": [len(d) for d in domains],
                     "distinct_column_matching": True,
                     "unassigned_source_mask_bits": 8 * (8 - depth),
                     "unit_count": len(units), "formula_sha256": sha(path),
                     "formula_bytes": path.stat().st_size})
    save(HERE / "panel.json", {"status": "FROZEN_N41_SOURCE_PREFIX_PANEL",
                               "candidate_id": None, "rng_seed": 20261012,
                               "public_target": fixture["public_target"],
                               "raw_preimage_index": fixture["raw_preimage_index"],
                               "source_formula_sha256": sha(XCNF), "rows": rows})
    paths = [Path(__file__), XCNF, FIXTURE, BUILD, SOURCE / "fourpair_v2.py", SOLVER,
             HERE / "panel.json"] + [HERE / f"{row['label']}.xcnf" for row in rows]
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_N41_PREFIX_PUBLIC_QUERIES", "candidate_id": None,
        "one_worker": True, "solver_flags": FLAGS, "per_case_parent_cap_ns": CASE_CAP_NS,
        "combined_rss_cap_bytes": RSS_CAP,
        "sources": {str(path): sha(path) for path in paths}})
    print("FROZEN_PANEL", len(rows), flush=True)


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    panel = json.loads((HERE / "panel.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    parent = psutil.Process()
    receipts = []
    for case in panel["rows"]:
        label = case["label"]
        stdout = HERE / f"{label}.stdout"
        stderr = HERE / f"{label}.stderr"
        peak = 0
        stop = None
        start = time.monotonic_ns()
        with stdout.open("x") as out, stderr.open("x") as err:
            child = subprocess.Popen([str(SOLVER), *FLAGS, str(HERE / f"{label}.xcnf")],
                                     stdout=out, stderr=err)
            process = psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
                    if peak > RSS_CAP:
                        stop = "RSS_CAP"
                except psutil.NoSuchProcess:
                    pass
                if time.monotonic_ns() - start > CASE_CAP_NS:
                    stop = "WALL_CAP"
                if stop:
                    child.kill()
                    break
                time.sleep(0.025)
            code = child.wait()
        wall = time.monotonic_ns() - start
        lines = stdout.read_text(errors="replace").splitlines()
        terminals = [line for line in lines if line.startswith("s ")]
        terminal = terminals[-1] if terminals else None
        status = ("SAT_PENDING_REPLAY" if terminal == "s SATISFIABLE" else
                  "UNSAT" if terminal == "s UNSATISFIABLE" else "BOUNDED_UNKNOWN")
        receipt = {"label": label, "status": status, "terminal": terminal,
                   "stop_reason": stop, "exit_code": code, "wall_ns": wall,
                   "peak_combined_rss_bytes": peak,
                   "restart_rows": sum(line.startswith("c rst") for line in lines),
                   "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
                   "formula_sha256": case["formula_sha256"]}
        save(HERE / f"{label}.receipt.json", receipt)
        receipts.append(receipt)
        print(label, status, round(wall / 1e9, 3), flush=True)
    save(HERE / "summary.json", {"status": "COMPLETE_BOUNDED_N41_PREFIX_PANEL",
                                 "candidate_id": None,
                                 "protocol_sha256": sha(HERE / "protocol.json"),
                                 "receipts": receipts})


if __name__ == "__main__":
    {"prepare": prepare, "run": run}[sys.argv[1]]()
