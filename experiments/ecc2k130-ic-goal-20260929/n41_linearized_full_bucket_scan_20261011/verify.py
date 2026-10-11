"""Bind frozen inputs, capped attempts, exact join, and independent replay."""

import hashlib
import json
from pathlib import Path

import run

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    p, r = load("protocol.json"), load("result.json")
    ip, ir = load("inverse_protocol.json"), load("inverse_result.json")
    rp, rr = load("retry_protocol.json"), load("retry_result.json")
    audit = load("audit.json")
    paths = {"source": HERE / "run.py", "geometry": run.GEOMETRY,
             "prior": run.PRIOR, "targets": HERE / "targets.json",
             "runtime": HERE / "sage_runtime_info.json"}
    assert p["sha256"] == {k: sha(v) for k, v in paths.items()}
    assert r["source_sha256"] == sha(HERE / "run.py")
    assert r["protocol_sha256"] == sha(HERE / "protocol.json")
    ipaths = {"source": HERE / "inverse_join.py", "field": HERE / "run.py",
              "targets": HERE / "targets.json", "geometry": run.GEOMETRY,
              "first_result": HERE / "result.json"}
    assert ip["sha256"] == {k: sha(v) for k, v in ipaths.items()}
    assert ir["source_sha256"] == sha(HERE / "inverse_join.py")
    assert ir["protocol_sha256"] == sha(HERE / "inverse_protocol.json")
    rpaths = {"source": HERE / "retry_negative3.py", "run": HERE / "run.py",
              "protocol": HERE / "protocol.json", "targets": HERE / "targets.json",
              "first_result": HERE / "result.json"}
    assert rp["sha256"] == {k: sha(v) for k, v in rpaths.items()}
    assert rr["protocol_sha256"] == sha(HERE / "retry_protocol.json")
    assert audit["status"] == "PASS_EXACT_REPLAY"
    assert audit["result_sha256"] == sha(HERE / "result.json")
    assert audit["source_sha256"] == sha(HERE / "audit_sage.py")
    assert audit["positive_raw_group_sum"] and len(audit["selected_seed_panel"]) == 16
    assert len(r["rows"]) == len(ir["rows"]) == 8
    for a, b in zip(r["rows"], ir["rows"]):
        assert (a["kind"], a["option"]) == (b["kind"], b["option"])
        assert b["status"] == "COMPLETE" and b["query_ns"] <= 120_010_000_000
        assert b["left_coordinates"] == ir["left_distinct_coordinates"] == 1984
        assert a["query_ns"] <= 120_010_000_000
        ah = sorted((x["left_seed"], x["right_seed"], x["left_z"]) for x in a["hits"])
        bh = sorted((x["left_seed"], x["right_seed"], x["left_z"]) for x in b["hits"])
        if a["status"] == "COMPLETE":
            assert a["bucket_decisions"] == 1984*63 and ah == bh
    assert r["rows"][7]["status"] == rr["status"] == "CENSORED_TIME"
    assert r["rows"][7]["bucket_decisions"] == 90216
    assert rr["bucket_decisions"] == 78498
    assert ir["rows"][3]["hits"] == [{"left_seed": 16, "right_seed": 5,
                                        "left_z": 585190544792,
                                        "right_z": 1979731517413}]
    assert all(not row["hits"] for i, row in enumerate(ir["rows"]) if i != 3)
    assert max(r["peak_rss_bytes"], rr["peak_rss_bytes"],
               ir["peak_rss_bytes"]) < 4*1024**3
    print(json.dumps({"status": "PASS_COMPLETE_INVERSE_EIGHT_LIFTS",
                      "first_linearized_complete_lifts": 7,
                      "inverse_complete_lifts": 8,
                      "positive_hits": 1, "negative_hits": 0}))


if __name__ == "__main__":
    main()
