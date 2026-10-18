#!/usr/bin/env bash
# One true MutantXL memory-frontier draw. CPU-only engine on the GPU host.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
payload=${FRONTIER_PAYLOAD_DIR:-"$here/source/frontier"}
out=${1:?"usage: frontier_launch.sh NEW_OUTPUT_DIR [--controls-only]"}
mode=${2:-full}
if [ "$mode" != full ] && [ "$mode" != --controls-only ]; then echo 'invalid mode' >&2; exit 2; fi
if [ -e "$out" ]; then echo 'append-only output directory already exists' >&2; exit 2; fi
mkdir -p "$out"
out=$(cd "$out" && pwd)
start=$(date +%s)
# Reserve the timeout's final 10-second kill grace inside the 1200-second cap.
deadline=$((start+1190))
printf '%s\n' 'CPU-only native MutantXL closure on a high-RAM GPU host; no GPU acceleration claim.' > "$out/scope.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/started-utc.txt"
uname -a > "$out/host.txt"
for dep in timeout prlimit jq sha256sum awk; do
 if ! command -v "$dep" >/dev/null; then printf '{"status":"impeded","missing_tool":"%s"}\n' "$dep" > "$out/terminal-status.json"; exit 78; fi
done
timer=${FRONTIER_TIME_BIN:-/usr/bin/time}
if [ ! -x "$timer" ]; then printf '{"status":"impeded","missing_tool":"GNU time; provision explicitly before launch"}\n' > "$out/terminal-status.json"; exit 78; fi
(cd "$payload" && sha256sum -c payload.sha256) > "$out/payload-verification.txt" 2>&1
sha256sum "$0" > "$out/launcher.sha256"
export RAYON_NUM_THREADS=1 OMP_NUM_THREADS=1 F4_F2_MAX_ROWS=50000000 F4_F2_MAX_COLS=50000000
export F4_F2_ECHELON=host
run_phase() {
 local name=$1 seconds=$2 address_space=$3; shift 3
 printf '%q ' "$@" > "$out/$name.command.txt"; printf '\n' >> "$out/$name.command.txt"
 set +e
 "$timer" -o "$out/$name.resources.txt" -f '{"elapsed_seconds":%e,"user_seconds":%U,"system_seconds":%S,"max_rss_kib":%M,"major_faults":%F,"file_inputs":%I,"file_outputs":%O,"exit_status":%x}' \
  timeout --signal=TERM --kill-after=10s "${seconds}s" prlimit --as="$address_space" -- "$@" > "$out/$name.stdout.jsonl" 2> "$out/$name.stderr"
 phase_status=$?
 set -e
 printf '%s\n' "$phase_status" > "$out/$name.exit"
 return "$phase_status"
}
if ! run_phase control-unsat 60 4000000000 "$payload/dreg_closure" --to 4 --max-cols 70000 --draw 2 "$payload/control-m4-5-2.jsonl"; then
 echo '{"status":"instrument_gate_failed","gate":"tiny_unsat_runtime"}' > "$out/terminal-status.json"; exit 2
fi
if ! jq -e -s 'length==1 and .[0].m==4 and .[0].n_vars==18 and any(.[0].scan[]; .closure_refuted==true)' "$out/control-unsat.stdout.jsonl" > "$out/control-unsat.validation.txt"; then
 echo '{"status":"instrument_gate_failed","gate":"tiny_unsat_semantics"}' > "$out/terminal-status.json"; exit 2
fi
if ! run_phase control-sat 60 4000000000 "$payload/dreg_closure" --satisfiable --to 4 --max-cols 70000 --draw 0 "$payload/control-m4-5-2.jsonl"; then
 echo '{"status":"instrument_gate_failed","gate":"tiny_sat_runtime"}' > "$out/terminal-status.json"; exit 2
fi
if ! jq -e -s 'length==1 and .[0].refuted_satisfiable==false and .[0].solutions>0 and all(.[0].scan[]; .xl_refuted==false and .closure_refuted==false and .saturated==true)' "$out/control-sat.stdout.jsonl" > "$out/control-sat.validation.txt"; then
 echo '{"status":"instrument_gate_failed","gate":"tiny_sat_soundness"}' > "$out/terminal-status.json"; exit 2
fi
if [ "$mode" = --controls-only ]; then echo '{"status":"controls_passed_only","frontier_executed":false,"gpu_acceleration":false}' > "$out/terminal-status.json"; exit 0; fi
host_bytes=$(awk '/^MemTotal:/{printf "%.0f",$2*1024}' /proc/meminfo)
effective_bytes=$host_bytes
cgroup_limit=unknown
if [ -r /sys/fs/cgroup/memory.max ]; then
 cgroup_limit=$(cat /sys/fs/cgroup/memory.max)
 if [ "$cgroup_limit" != max ]; then effective_bytes=$(awk -v a="$host_bytes" -v b="$cgroup_limit" 'BEGIN{printf "%.0f",a<b?a:b}'); fi
fi
frontier_as_cap=$(awk -v n="$effective_bytes" 'BEGIN{c=n-32000000000; if(c>200000000000)c=200000000000; printf "%.0f",c}')
printf '{"host_total_bytes":%s,"cgroup_limit":"%s","effective_limit_bytes":%s,"required_minimum_bytes":192000000000,"process_address_space_cap_bytes":%s}\n' "$host_bytes" "$cgroup_limit" "$effective_bytes" "$frontier_as_cap" > "$out/memory-gate.json"
if ! awk -v n="$effective_bytes" 'BEGIN{exit !(n>=192000000000)}'; then
 echo '{"status":"impeded","reason":"original frontier requires at least 192000000000 effective host RAM bytes","frontier_executed":false}' > "$out/terminal-status.json"; exit 78
fi
remaining=$((deadline-$(date +%s)))
if [ "$remaining" -le 0 ]; then echo '{"status":"censored","reason":"global1200s_budget_before_frontier","frontier_executed":false}' > "$out/terminal-status.json"; exit 124; fi
if ! run_phase original-m3-19-7-degree5 "$remaining" "$frontier_as_cap" "$payload/dreg_closure" --to 5 --max-cols 800000 --draw 0 "$payload/original-m3-19-7.jsonl"; then
 printf '{"status":"censored_or_failed","exit_status":%s,"frontier_executed":true,"degree_claim":"unmeasured by this attempt","gpu_acceleration":false}\n' "$phase_status" > "$out/terminal-status.json"; exit "$phase_status"
fi
if ! jq -e -s 'length==1 and .[0].m==3 and .[0].n==19 and .[0].ell==7 and .[0].n_vars==40 and .[0].draw==0 and any(.[0].scan[]; .degree==4 and .saturated==true and .closure_refuted==false) and any(.[0].scan[]; .degree==5 and (.closure_refuted==true or .saturated==true))' "$out/original-m3-19-7-degree5.stdout.jsonl" > "$out/frontier.validation.txt"; then
 echo '{"status":"measurement_gate_failed","reason":"missing_degree5_or_unexpected_control_bound","frontier_executed":true,"degree_claim":"not_admitted"}' > "$out/terminal-status.json"; exit 2
fi
echo '{"status":"original_frontier_draw_completed","frontier_executed":true,"scope":"One committed MutantXL closure-refutation draw; not F4 solving degree, full ECDLP, or GPU acceleration. Independent replay still owed."}' > "$out/terminal-status.json"
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/finished-utc.txt"
