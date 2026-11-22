"""Independently replay every raw-code assignment against saved certificates."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "n41_n131_macaulay_family_gate_20261019"))
from macaulay import Field, source_basis, source_value

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "audit_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_BLOCK_CERTIFICATE_AUDIT"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError("wall cap")))
signal.alarm(cfg["wall_cap_seconds"])
start = time.monotonic()

lines = Path(cfg["sources"]["resultant_input"]["path"]).read_text().splitlines()
assert lines[0] == "FREECODE 25 281 13"
valid = {}
for line in lines[1:282]:
    _, code, p, q = line.split()
    valid[int(code)] = (int(p), int(q))
terms = {0: {}, 1: {}}
for line in lines[282:]:
    parts = line.split()
    if parts[0] == "C" and int(parts[1]) in terms:
        terms[int(parts[1])][int(parts[2]), int(parts[3])] = int(parts[4])
F = Field(41, 9)
bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
pb = source_basis(F, 112, bits, 12)
qb = source_basis(F, 112, bits, 24)


def powers(value):
    out = [1]
    for _ in range(4):
        out.append(F.mul(out[-1], value))
    return out


def direct_value(target, pp, qq):
    out = 0
    for (i, j), c in terms[target].items():
        out ^= F.mul(F.mul(c, pp[i]), qq[j])
    return out


q_powers = [powers(source_value(code, qb)) for code in range(1024)]
stored = json.loads((HERE / "block_result.json").read_text())
assert stored["status"] == "COMPLETE_N41_MACAULAY_BLOCK_PANEL"
rows = []
for saved in stored["rows"]:
    if not saved["reject"]:
        continue
    width = saved["block_width"]
    base = saved["block_start"]
    target = saved["target_index"]
    by_bit = {}
    for bit, multiplier in saved["certificate_rows"]:
        by_bit.setdefault(bit, []).append(multiplier)
    checked = 0
    raw_roots = 0
    for pcode in range(base, base + (1 << width)):
        pp = powers(source_value(pcode, pb))
        for qcode, qq in enumerate(q_powers):
            packed = (pcode - base) | (qcode << width)
            value = direct_value(target, pp, qq)
            raw_roots += value == 0
            parity = 0
            for bit, masks in by_bit.items():
                if value >> bit & 1:
                    for mask in masks:
                        parity ^= mask & packed == mask
            assert parity == 1, (target, width, pcode, qcode)
            checked += 1
    assert raw_roots == 0
    rows.append({"target_index": target, "block_width": width,
                 "block_start": base, "raw_assignments_checked": checked,
                 "raw_roots": raw_roots, "certificate_rows": len(saved["certificate_rows"])})
    print(json.dumps(rows[-1], sort_keys=True), flush=True)
assert len(rows) == 5
signal.alarm(0)
out = {"status": "PASS_N41_BLOCK_CERTIFICATE_EXHAUSTIVE_AUDIT",
       "candidate_id": None, "rows": rows,
       "wall_seconds": time.monotonic() - start,
       "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256": sha(HERE / "audit_protocol.json"),
       "script_sha256": sha(__file__)}
(HERE / "audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: out[k] for k in ("status", "wall_seconds", "peak_rss_raw")}, sort_keys=True))
