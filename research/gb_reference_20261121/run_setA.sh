#!/usr/bin/env bash
# Set A: registry phase-1 PKM baseline commands, m = 2..9, plus --export.
# Each m runs under the trunk watchdog (12 GiB, 3600 s = registry cell wall).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PILOT=${PILOT:-$HERE/../../suite/target/release/examples/pkm_tower_pilot}
TRUNK=${TRUNK:-/home/user/workspace}
OUT=${OUT:-$HERE/data/setA}
mkdir -p "$OUT"
for m in 2 3 4 5 6 7 8 9; do
  tmin=$(python3 -c "import math;print(max(1,math.ceil(math.log2($m))))")  # = lead_sweep plan
  python3 "$TRUNK/tools/lead_sweep.py" watch --mem-gib 12 --wall 3600 --log "$OUT/m$m.log" -- \
    "$PILOT" --p 786433 --m $m --kinds kummer,dickson,isogeny --t-min $tmin --max-t 8 \
    --max-t-m3 8 --max-t-m4 8 --budget 60 --seed 1347112276 --planted 3 --random 3 \
    --ladder-t none --controls tower,null,naive --out "$OUT/f4fp-m$m.jsonl" --export "$OUT/systems" \
    > "$OUT/m$m.watch.json"
  echo "m=$m $(python3 -c "import json;d=json.load(open('$OUT/m$m.watch.json'));print(d['status'],d['wall_seconds'],d['peak_rss_gib'])")"
done
