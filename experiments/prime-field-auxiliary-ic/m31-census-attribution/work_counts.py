"""Decompose archived times using exact rationals on the reported decimal inputs."""
import json
from fractions import Fraction
from statistics import median

from replay import ARCHIVE_REV, FIXTURE, digests, read

def record(arm, seed):
    row = json.loads(read(f"{FIXTURE}/{arm}_seed{seed}.audited.json"), parse_float=Fraction)
    assert row["seed"] == seed and row["label"] == arm
    return row


def rounded(x):
    return round(float(x), 8)


def main():
    rows = []
    batch_wall, rho_wall = [], []
    for seed in range(3):
        old, control, batch, rho = (record(arm, seed) for arm in
                                    ("v1_chain", "v2_chain", "v2_batch", "rho"))
        logs = [read(f"{FIXTURE}/{arm}_seed{seed}.relations.jsonl")
                for arm in ("v1_chain", "v2_chain", "v2_batch")]
        for data, log in zip((old,control,batch), logs):
            assert len(log.splitlines()) == data["relations"]
        assert logs[0] == logs[1] and logs[2] != logs[1]
        assert old["queries"] == control["queries"] and old["weights"] == control["weights"]
        t, u = control["loop_seconds"], batch["loop_seconds"]
        q, r = control["queries"], batch["queries"]
        volume = Fraction(q,r)
        rate = (t/q)/(u/r)
        assert volume * rate == t/u
        padding = batch["generated_targets"] - r
        assert 0 <= padding < batch["batch_width"]
        b, h = batch["end_to_end_seconds"], rho["end_to_end_seconds"]
        batch_wall.append(b)
        rho_wall.append(h)
        rows.append(dict(seed=seed, control_queries=q, batch_queries=r, unused_batch_tail=padding,
                         same_rows_v1_to_v2=True,
                         same_count_wall_ratio=rounded(old["end_to_end_seconds"]/control["end_to_end_seconds"]),
                         control_loop_ns_per_query=rounded(t/q*10**9),
                         batch_loop_ns_per_query=rounded(u/r*10**9),
                         work_ratio=rounded(volume), per_query_ratio=rounded(rate),
                         loop_ratio=rounded(t/u),
                         batch_vs_rho_wall_ratio=rounded(b/h)))
    print(json.dumps(dict(archive_revision=ARCHIVE_REV, rows=rows,
                          ratio_of_median_wall_times=rounded(median(batch_wall)/median(rho_wall)),
                          median_paired_wall_ratio=rounded(median(b/h for b,h in zip(batch_wall,rho_wall))),
                          sha256=digests),indent=2))

if __name__ == "__main__":
    main()
