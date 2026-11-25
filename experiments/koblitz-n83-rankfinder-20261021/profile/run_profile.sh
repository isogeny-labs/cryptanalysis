#!/bin/sh
# Usage: run_profile.sh <binary> <seed> <mode> <out-prefix>   (local diagnostic; M38, arm.py's rank env)
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d)
python3 -c "import json;p=json.load(open('$HERE/inputs/cold_targets.json'))['points'][0]['point'];print(json.dumps(p,separators=(',',':')))" > "$T/points.jsonl"
env -i PATH=/usr/bin:/bin LC_ALL=C RAYON_NUM_THREADS=1 KIC_THREADS=1 KIC_RHO_THREADS=1 OMP_NUM_THREADS=1 \
  KIC_RANK_THREADS=1 KIC_TARGET_THREADS=1 KIC_INDEX_DIGEST=1 KIC_ROOT_TABLE=compact KIC_STATE_FOLD=1 KIC_FOLD_PLANT=0 \
  KIC_INDEX_CANON=lift KIC_SCAN_SELFTEST=full KIC_TARGET_CANON=lift KIC_SCAN_ORDER=feistel KIC_PROBE_PIPELINE=prefetch \
  KIC_LOG_TABLE_OUT="$T/logs.json" KIC_RANK_CANON=lift KIC_RANK_ORDER=feistel KIC_RANK_PROBE=target KIC_RANK_SOLVE=frame \
  KIC_RANKPROF="$3" taskset -c 3 "$1" "$HERE/snapshots/closure/base_n83_closure_M38.jsonl" "$T/points.jsonl" "$2" "$T/ic.jsonl" \
  > "$4.stdout.jsonl" 2> "$4.stderr.txt"
rm -rf "$T"
grep rankprof= "$4.stderr.txt"
tail -1 "$4.stdout.jsonl" | python3 -c "import json,sys;s=json.loads(sys.stdin.read());print('rank_stage_ms',s['timing_ms']['rank_stage'],'probes',s['rank_probes_total'])"
