#!/usr/bin/env python3
"""CT138: independent same-cohort width-sweep auditor, no C++ arithmetic imported.

Reuses a *separate* original CT136 Python MT64/EC verifier with byte guard.
The raw generated schema/width labels are checked BEFORE normalization.
"""
import csv
import hashlib
import importlib.util
import json
import pathlib
import random
import statistics
import sys
import tempfile

BASE = pathlib.Path(__file__).resolve().parent
WIDTHS = (16, 32, 64)
SEEDS = (20261340, 20261341, 20261342, 20261343)
COUNT = 32
VERIFIER_SHA256 = "ce3a9e5af959ad5ec3a81ce78151587a099fa8f86029bc7fa059bf9a384abc2f"
SOURCE_ARMS = ("source_bsgs", "source_neg_rho", "source_batch32_rho")
TARGET_ARMS = ("target_glv_rho", "target_batch32_rho")
ARMS = ("source_bsgs", "source_neg_rho", "target_glv_rho",
        "source_batch32_rho", "target_batch32_rho")

def need(ok, label):
    if not ok:
        raise ValueError(label)

def original_verifier():
    path = BASE / "ct136_verify.py"
    need(hashlib.sha256(path.read_bytes()).hexdigest() == VERIFIER_SHA256,
         "original independent Python verifier hash mismatch")
    spec = importlib.util.spec_from_file_location("ct136_independent", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def normalize(raw, width, seed):
    need(width in WIDTHS and seed in SEEDS, "unapproved cohort")
    prefix = "schema,ct138-width" + str(width) + "-cold-v1\n"
    need(raw.startswith(prefix), "raw width/schema mismatch")
    need(raw.count(prefix) == 1, "duplicate schema")
    need(raw.count("source_batch" + str(width) + "_rho") == 2*COUNT+1,
         "source batch-label count mismatch")
    need(raw.count("target_batch" + str(width) + "_rho") == 2*COUNT+1,
         "target batch-label count mismatch")
    result = raw.replace(prefix, "schema,ct136-batched-cold-v1\n", 1)
    result = result.replace("source_batch" + str(width) + "_rho", "source_batch32_rho")
    result = result.replace("target_batch" + str(width) + "_rho", "target_batch32_rho")
    return result

def audit_directory(directory):
    verify = original_verifier()
    verify.preflight()
    paths = { (w,s): directory/f"width{w}-{s}.csv"
             for w in WIDTHS for s in SEEDS }
    need(all(p.is_file() for p in paths.values()), "missing width or cohort")
    need({p.name for p in directory.glob("*.csv")} ==
         {p.name for p in paths.values()}, "extra raw CSV")
    expected_sequence=(
        "20261340:16", "20261340:32", "20261340:64",
        "20261341:32", "20261341:64", "20261341:16",
        "20261342:64", "20261342:16", "20261342:32",
        "20261343:64", "20261343:32", "20261343:16")
    need(tuple((directory.parent/"sequence.txt").read_text().splitlines()) ==
         expected_sequence, "rotating width order or missing processes")
    host_bytes=(directory.parent/"host.txt").read_bytes()
    need(b"g++" in host_bytes,
         "missing native host/compiler receipt")
    peak_kb={}
    for (width,seed), path in paths.items():
        need(path.with_suffix(".stderr").is_file(), "missing stderr capture")
        time_path=path.with_suffix(".time")
        need(time_path.is_file(), "missing process resource receipt")
        words=dict(token.split("=",1) for token in time_path.read_text().split()
                   if "=" in token)
        need(set(words)=={"wall_seconds","maxrss_kb"}, "resource receipt schema")
        try:
            wall=float(words["wall_seconds"])
            rss=int(words["maxrss_kb"])
        except (ValueError,OverflowError) as exc:
            raise ValueError("invalid resource receipt") from exc
        need(0 <= wall < 120 and 0 < rss < 2097152, "resource bounds")
        peak_kb[f"{width}:{seed}"]=rss
    reports = []
    per_target = {}
    aa = { (w,arm): [] for w in WIDTHS for arm in ARMS}
    sabotage_counts={}
    with tempfile.TemporaryDirectory(prefix="ct138-independent-") as folder:
        for width in WIDTHS:
            for seed in SEEDS:
                path=paths[(width,seed)]
                raw_bytes=path.read_bytes()
                raw=raw_bytes.decode("utf-8")
                normalized=normalize(raw,width,seed)
                temp=pathlib.Path(folder)/f"normal-{width}-{seed}.csv"
                temp.write_text(normalized)
                result=verify.audit(temp,seed,COUNT)
                result["width"]=width
                result["raw_sha256"]=hashlib.sha256(raw_bytes).hexdigest()
                reports.append({k:v for k,v in result.items() if k!="paired"})
                rows=list(csv.reader(normalized.splitlines()))
                for index in range(COUNT):
                    seg=rows[3+10*index:3+10*(index+1)]
                    by_arm={arm:[] for arm in ARMS}
                    for line in seg:
                        by_arm[line[2]].append(int(line[7]))
                    need(all(len(by_arm[a])==2 for a in ARMS), "ABBA missing repeated arm")
                    for arm in ARMS:
                        ns1,ns2=by_arm[arm]
                        aa[(width,arm)].append(ns1/ns2)
                    per_target[(width,seed,index)] = {
                        a:sum(by_arm[a]) for a in ARMS
                    }
                if seed == SEEDS[0]:
                    sabotage_counts[width]=verify.sabotage(temp,seed,COUNT)
                    need(sabotage_counts[width]==11,"independent sabotage controls")
        # Explicit width-label mutation must be rejected before normalization.
        for width in WIDTHS:
            path=paths[(width,SEEDS[0])]
            bad=path.read_text().replace(
                "source_batch" + str(width) + "_rho",
                "source_batch999_rho",1)
            try:
                normalize(bad,width,SEEDS[0])
            except ValueError:
                pass
            else:
                raise ValueError("invalid batch-width label was accepted")

    totals={}
    for w in WIDTHS:
        totals[w]={arm:sum(per_target[(w,s,i)][arm]
                           for s in SEEDS for i in range(COUNT))
                   for arm in ARMS}
    ratios={}
    for w in WIDTHS:
        so=min(totals[w][a] for a in SOURCE_ARMS)
        ta=min(totals[w][a] for a in TARGET_ARMS)
        ratios[w]=so/ta
    # Compare each fixed *algorithm-width* arm's whole-cohort time, never
    # choose an oracle winner independently on each target.
    best_source=min((totals[w][a],w,a) for w in WIDTHS for a in SOURCE_ARMS)
    best_target=min((totals[w][a],w,a) for w in WIDTHS for a in TARGET_ARMS)
    overall=best_source[0]/best_target[0]
    # Fixed-cohort descriptive paired bootstrap only; no independent-sample CI.
    rng=random.Random(138); ids=[(s,i) for s in SEEDS for i in range(COUNT)]
    bootstrap=[]
    for _ in range(400):
        sampled=[ids[rng.randrange(len(ids))] for __ in ids]
        src=min(sum(per_target[(w,s,i)][a] for s,i in sampled)
                for w in WIDTHS for a in SOURCE_ARMS)
        dst=min(sum(per_target[(w,s,i)][a] for s,i in sampled)
                for w in WIDTHS for a in TARGET_ARMS)
        bootstrap.append(src/dst)
    bootstrap.sort()
    return {
      "schema":"ct138-batch-width-audit-v1",
      "standing":"[pcc:unverified]",
      "scope":"selected 31-bit CM-neighbor; no original-prime Jacobian full-chain",
      "widths":list(WIDTHS),"seeds":list(SEEDS),
      "public_target_count":len(ids),
      "complete_recoveries":len(WIDTHS)*len(ids)*10,
      "reports":reports,
      "peak_process_rss_kb":peak_kb,
      "host_sha256":hashlib.sha256(host_bytes).hexdigest(),
      "total_ns":totals,
      "per_width_best_source_over_target":ratios,
      "best_source_ns_width_arm":list(best_source),
      "best_target_ns_width_arm":list(best_target),
      "best_source_over_best_target":overall,
      "descriptive_paired_bootstrap_95":bootstrap[9:10]+bootstrap[389:390],
      "aa_median":{str(w)+":"+a:statistics.median(aa[(w,a)]) for w in WIDTHS for a in ARMS},
      "mutations_rejected":sabotage_counts,
      "scope_note":"No source curve selection charge; no IC or original 695/701 Jacobian cold cost; no PCC signature"
    }

def main():
    need(len(sys.argv)==2,"usage: ct138_verify.py DIRECTORY")
    report=audit_directory(pathlib.Path(sys.argv[1]))
    print(json.dumps(report,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
