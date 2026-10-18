#!/usr/bin/env bash
set -uo pipefail
study=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
out=${1:?output directory}
mkdir -p "$out"
date -u +%FT%TZ > "$out/started.utc"
lscpu > "$out/lscpu.txt"
cat /proc/meminfo > "$out/meminfo.txt"
uname -a > "$out/uname.txt"
set +e
bash "$study/frontier_highram.sh" "$out/frontier" > "$out/frontier-launch.stdout" 2> "$out/frontier-launch.stderr"
rc=$?
printf '%s\n' "$rc" > "$out/frontier-pipeline.exit"
printf '{"frontier_exit":%s,"gpu_acceleration":false,"scope":"CPU-only same frozen closure draw"}\n' "$rc" > "$out/execution-status.json"
date -u +%FT%TZ > "$out/finished.utc"
exit "$rc"
