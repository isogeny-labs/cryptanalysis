#!/usr/bin/env python3
"""Summarize the pre-freeze local exactness runs into `inputs/local_exactness.json`.

LOCAL CORRECTNESS CHECK on the cloud-agent VM, before the protocol froze.
`raw/exactness/*.stdout.txt` are `arm.py` wrapper outputs (the Tier 1
template's `arm.py` for K600 and M38, the parent's for M10 because only its
protocol has the M10 arms), each with the full per-process gate set of that
wrapper (base hash, states, slots, entries, logical-state and table-map
digests, layout digests, Q0 or point solved and verified):

* `new-*`: the derived producer `ic_online_indexbuild_r770` built from the
  frozen derivation (toolchain 1.97, local);
* `old-kM38I-1201`: the row's producer on the same rank seed as
  `new-kM38I-1201`.

The summary checks, against the parent protocol's frozen values: the layout
digests (`stored_states_blake3`, `table_slots_blake3`) and the logical-state
and table-map digests on K600, M38 and M10; the Q0 identity (relation,
scalar, probes) on all three bases; the written rank tables equal to the
frozen verified tables (M38 and M10); and, for seed 1201 on M38, the rank
relation digest, per-attempt probe vector, root calls and counters of the
derived producer equal to the row's.
"""

import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
OUT = EXPERIMENT / "inputs" / "local_exactness.json"
PARENT = EXPERIMENT.parent / "koblitz-n83-closure-indexlift-20261019" / "protocol.json"
PARENT_SHA256 = "ff5b4cbfba8097cf1c1125f500f4f75ac82bd2d6518fae5da4976e5eec64a9c1"
BASE_OF = {"cPI": "K600", "cM10I": "M10", "kM10I": "M10", "cM38I": "M38", "kM38I": "M38"}
RANK_KEYS = ("rank_relations_blake3", "rank_attempt_probes", "rank_root_calls_total", "rank_padd_fallback_states",
             "rank_padd_irregular_inputs", "rank_padd_resolved_hits", "rank_padd_swapped_pairs", "rank_frame_builds",
             "rank_attempts", "rank")


def load(path):
    lines = path.read_text().splitlines()
    raw_bytes = base64.b64decode(next(l[8:] for l in lines if l.startswith("raw_b64=")))
    line = next(l for l in reversed(lines) if "raw_result_sha256=" in l)
    if dict(w.split("=", 1) for w in line.split() if "=" in w)["raw_result_sha256"] != \
            hashlib.sha256(raw_bytes).hexdigest():
        raise SystemExit("raw digest differs: %s" % path.name)
    raw = json.loads(raw_bytes)
    return raw, next(r for r in raw["records"] if r.get("kind") == "compact_orbit_dlp_summary")


def main():
    if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA256:
        raise SystemExit("parent protocol differs from its pinned digest")
    bases = json.loads(PARENT.read_text())["online"]["bases"]
    rows, ok = {}, True
    for path in sorted((HERE / "raw" / "exactness").glob("*.stdout.txt")):
        name = path.name[:-len(".stdout.txt")]
        raw, summary = load(path)
        base = BASE_OF[raw["arm"]]
        spec = bases[base]
        digest = summary["index_digest"]
        layout = all(digest[k] == spec["layout_digest"][k] for k in ("stored_states_blake3", "table_slots_blake3"))
        index = all(digest[k] == spec["index_digest"][k] for k in ("logical_states_blake3", "table_map_sum64",
                                                                     "table_map_xor64", "table_entries"))
        row = {"arm": raw["arm"], "base": base, "binary": "derived" if name.startswith("new") else "row",
               "wrapper_issues": raw["issues"], "index_build_pipeline": summary.get("index_build_pipeline"),
               "layout_digests_equal_frozen": layout, "index_digests_equal_frozen": index,
               "index_build_ms_local": summary["timing_ms"]["index_build"],
               "scan_selftest": {k: summary["scan_order_selftest"][k] for k in ("bijection", "mode", "ms")},
               "probes": raw["fields"]["ops"], "relation": raw["fields"]["relation"],
               "scalar": str(raw["fields"]["recovered_scalar"])}
        if raw["panel"] == "q0":
            want = spec["q0_identity"]
            row["q0_identity_equal_frozen"] = (row["relation"] == want["relation"] and row["scalar"] == want["scalar"]
                                               and row["probes"] == want["probes_folded"])
            ok &= row["q0_identity_equal_frozen"]
        if raw["kind"] == "ic_rank":
            row["rank_table_equal_frozen"] = raw["fields"]["logs_equal_archived"]
            ok &= row["rank_table_equal_frozen"] is True
        ok &= not raw["issues"] and layout and index and summary["scan_order_selftest"]["bijection"] is True
        rows[name] = (row, summary)
    _, new_rank = rows["new-kM38I-1201"]
    _, old_rank = rows["old-kM38I-1201"]
    same_rank = {k: new_rank.get(k) == old_rank.get(k) for k in RANK_KEYS}
    ok &= all(same_rank.values())
    out = {"schema": 1, "label": "LOCAL CORRECTNESS on the cloud-agent VM before the protocol froze; no timing claim",
           "parent_protocol_sha256": PARENT_SHA256, "processes": {k: v[0] for k, v in rows.items()},
           "bases_covered": sorted({v[0]["base"] for v in rows.values()}),
           "seed_1201_m38_rank_stage_identical_row_vs_derived": same_rank, "all_pass": ok}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": ok, "bases": out["bases_covered"], "rank_identical": same_rank}, sort_keys=True))


if __name__ == "__main__":
    main()
