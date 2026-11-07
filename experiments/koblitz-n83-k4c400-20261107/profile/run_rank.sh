#!/bin/sh
# Usage: run_rank.sh <binary> <seed> <out-prefix> [wrapper...]   local diagnostic cold arm (M38, cached table), arm.py's ic_cold env
set -eu
HERE=/home/user/cryptanalysis/experiments/koblitz-n83-rankfinder-20261021
BIN=$1; SEED=$2; OUT=$3; shift 3
T=$(mktemp -d)
python3 -c "import json;p=json.load(open('$HERE/inputs/cold_targets.json'))['points'][0]['point'];print(json.dumps(p,separators=(',',':')))" > "$T/points.jsonl"
env -i PATH=/usr/bin:/bin LC_ALL=C RAYON_NUM_THREADS=1 KIC_THREADS=1 KIC_RHO_THREADS=1 OMP_NUM_THREADS=1 \
  KIC_RANK_THREADS=1 KIC_TARGET_THREADS=1 KIC_INDEX_DIGEST=1 KIC_ROOT_TABLE=compact KIC_STATE_FOLD=1 KIC_FOLD_PLANT=0 \
  KIC_INDEX_CANON=lift KIC_SCAN_SELFTEST=full KIC_TARGET_CANON=lift KIC_SCAN_ORDER=feistel KIC_PROBE_PIPELINE=prefetch \
  KIC_LOG_TABLE_OUT="$T/logs.json" KIC_RANK_CANON=lift KIC_RANK_ORDER=feistel KIC_RANK_PROBE=target KIC_RANK_SOLVE=frame \
  "$@" "$BIN" "$BASE" "$T/points.jsonl" "$SEED" "$T/ic.jsonl" \
  > "$OUT.stdout.jsonl" 2> "$OUT.stderr.txt"
cp "$T/logs.json" "$OUT.logs.json" 2>/dev/null || true; rm -rf "$T"
tail -1 "$OUT.stdout.jsonl" | python3 -c "
import json,sys; s=json.loads(sys.stdin.read()); t=s['timing_ms']
print('timing_ms', json.dumps(t)); print('selftest', s['scan_order_selftest']); print('verified', s.get('every_log_verified_against_representative'), 'targets', s.get('solved'))"
