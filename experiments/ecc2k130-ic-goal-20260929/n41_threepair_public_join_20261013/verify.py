"""Independent source-cardinality and frozen-bucket coverage audit."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "public_protocol.json").read_text())
    assert protocol["source_hashes_sha256"]["pairs.tsv"] == sha(SOURCE)
    states = []
    with SOURCE.open() as stream:
        assert stream.readline().split() == ["ECC2K41_ALLSEED4", "4", "4"]
        for line in stream:
            row = line.split()
            if row[0] == "S" and row[1] == "0":
                sid = int(row[2])
                assert sid == len(states)
                states.append(tuple(sorted((int(row[5]), int(row[6])))))
    assert len(states) == 30952
    freq = Counter(column for a,b in states for column in (a,b))
    pair_freq = Counter(states)
    eligible = [len(states)-freq[a]-freq[b]+pair_freq[(a,b)] for a,b in states]
    expected_by_bucket = {bucket: sum(eligible[bucket::64]) for bucket in range(64)}
    labels = ("public_retry1", "fast", "tail")
    buckets = []
    total_probes = 0
    phase_detail = []
    for label in labels:
        run = json.loads((HERE / f"{label}_run.json").read_text())
        stdout_path = HERE / f"{label}_stdout.log"
        stderr_path = HERE / f"{label}_stderr.log"
        assert run["stdout_sha256"] == sha(stdout_path)
        assert run["stderr_sha256"] == sha(stderr_path)
        lines = stdout_path.read_text().splitlines()
        if label != "public_retry1":
            assert lines.pop(0) == "FIELD_SELFTEST_PASS 100000"
        assert lines.pop(0).startswith("SOURCE_PASS 30952 4 ")
        completed = []
        cumulative = 0
        for line in lines:
            if line.startswith("BUCKET_DONE "):
                parts = line.split()
                assert len(parts) == 7
                bucket, first, probes, xm, em = map(int, parts[1:6])
                assert first == len(range(bucket, len(states), 64))
                cumulative += expected_by_bucket[bucket]
                assert probes == cumulative and xm == 0 and em == 0
                completed.append(bucket)
            elif line.startswith("EXHAUSTED "):
                parts = line.split()
                assert len(parts) == 5 and label == "tail"
                assert list(map(int, parts[1:4])) == [cumulative, 0, 0]
            else:
                raise AssertionError(f"unexpected output line: {line}")
        assert completed == run["buckets_done"] and not run["hit_lines"]
        assert run["status"] == ("SOURCE_EXHAUSTED" if label == "tail" else "BOUNDED_UNKNOWN")
        buckets += completed
        total_probes += cumulative
        phase_detail.append({"label": label, "completed_buckets": len(completed),
                             "eligible_probes": cumulative, "wall_seconds": run["wall_seconds"],
                             "peak_observed_rss_bytes": run["peak_observed_rss_bytes"]})
    assert buckets == protocol["frozen_bucket_order"]
    assert sorted(buckets) == list(range(64))
    assert total_probes == sum(expected_by_bucket.values())
    result = {
        "status": "PASS_COMPLETE_N41_THREEPAIR_SOURCE_COVERAGE",
        "curve_id": protocol["curve_id"],
        "public_target_xy": protocol["public_target_xy"],
        "source_signed_states": len(states), "frozen_buckets": len(buckets),
        "eligible_ordered_pair_probes": total_probes,
        "x_matches": 0, "exact_matches": 0,
        "phase_detail": phase_detail,
        "input_sha256": {"source": sha(SOURCE),
                         "baseline_run": sha(HERE / "public_retry1_run.json"),
                         "fast_run": sha(HERE / "fast_run.json"),
                         "tail_run": sha(HERE / "tail_run.json"),
                         "coset": sha(HERE / "coset_result.json")},
    }
    with (HERE / "verify_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
