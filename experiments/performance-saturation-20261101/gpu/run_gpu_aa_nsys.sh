#!/usr/bin/env bash
# Byte-identical CUDA A/A calibration with post-timing Nsys diagnostics.
# Run only through a new, uniquely named Secure Runpod RTX 5090 pod.  This
# script creates a unique session below OUT_ROOT and never overwrites a row.
set -Eeuo pipefail
umask 077

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$SCRIPT_DIR/../../.." && pwd)
ANALYZER="$SCRIPT_DIR/analyze_gpu_aa_nsys.py"
EXPECTED_GPU="NVIDIA GeForce RTX 5090"
OUT_ARG=${1:?usage: run_gpu_aa.sh REPOSITORY_RELATIVE_OUT_ROOT [SESSION_ID]}
SESSION_ID=${2:-gpu-aa-$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM}

if [[ ! $SESSION_ID =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$ ]]; then
  echo "unsafe session id: $SESSION_ID" >&2
  exit 2
fi
if [[ $OUT_ARG = /* ]]; then
  OUT_ROOT=$(realpath -m "$OUT_ARG")
else
  OUT_ROOT=$(realpath -m "$REPO/$OUT_ARG")
fi
case "$OUT_ROOT/" in
  "$REPO"/*/) ;;
  *) echo "output root must be inside $REPO" >&2; exit 2 ;;
esac
mkdir -p "$OUT_ROOT"
SESSION="$OUT_ROOT/$SESSION_ID"
mkdir "$SESSION" || { echo "session already exists: $SESSION" >&2; exit 2; }
mkdir -p "$SESSION/raw" "$SESSION/profiles" "$SESSION/metadata"

BIN_DIR=$(mktemp -d /tmp/cryptanalysis-gpu-aa.XXXXXX)
runner_status="$SESSION/runner-exit.status"
cleanup() {
  local rc=$?
  if [[ -n ${SMI_PID:-} ]]; then
    kill "$SMI_PID" 2>/dev/null || true
    wait "$SMI_PID" 2>/dev/null || true
  fi
  printf '%s\n' "$rc" >"$runner_status"
  rm -rf -- "$BIN_DIR"
  exit "$rc"
}
trap cleanup EXIT INT TERM

if [[ ${GPU_STUDY_SECURE:-0} != 1 ]]; then
  echo "refusing: set GPU_STUDY_SECURE=1 only when cloud/runpod_pod.py requested --cloud SECURE" >&2
  exit 2
fi
if [[ -z ${RUNPOD_POD_ID:-} ]]; then
  echo "refusing: RUNPOD_POD_ID is absent; this calibration is scoped to an ephemeral Runpod pod" >&2
  exit 2
fi

cd "$REPO"
# cloud/runpod_pod.py already sources this, but direct invocation on its pod
# remains supported and idempotent.
# shellcheck source=../../../cloud/pod_env.sh
source cloud/pod_env.sh

for tool in cargo git nvidia-smi python3 realpath rustc sha256sum; do
  command -v "$tool" >/dev/null || { echo "missing required tool: $tool" >&2; exit 2; }
done

resolve_nsys() {
  local override=$1 candidate
  if [[ -n $override && -x $override ]]; then
    printf '%s\n' "$override"
    return 0
  fi
  if candidate=$(command -v nsys 2>/dev/null); then
    printf '%s\n' "$candidate"
    return 0
  fi
  shopt -s nullglob
  local candidates=(
    /opt/nvidia/nsight-systems/*/target-linux-x64/nsys
    /usr/local/cuda/bin/nsys
  )
  shopt -u nullglob
  for candidate in "${candidates[@]}"; do
    if [[ -x $candidate ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

NSYS_BIN=$(resolve_nsys "${NSYS:-}") || {
  echo "missing nsys; use an image with Nsight Systems CLI or set NSYS=/absolute/path/nsys" >&2
  exit 2
}

"$NSYS_BIN" --version >"$SESSION/metadata/nsys-version.txt" 2>&1
# Nsight Systems 2026.3.2 returns one after successfully printing its built-in
# report inventory.  Preserve that status and gate the inventory itself; no
# other nonzero status is accepted.
set +e
"$NSYS_BIN" stats --help-reports >"$SESSION/metadata/nsys-reports.txt" 2>&1
nsys_reports_rc=$?
set -e
printf '%s\n' "$nsys_reports_rc" >"$SESSION/metadata/nsys-reports.status"
if (( nsys_reports_rc != 0 && nsys_reports_rc != 1 )); then
  echo "nsys report inventory failed with status $nsys_reports_rc" >&2
  exit 2
fi
for report in cuda_gpu_kern_sum cuda_api_sum; do
  grep -q "$report" "$SESSION/metadata/nsys-reports.txt" || {
    echo "nsys does not provide required report $report" >&2
    exit 2
  }
done

mapfile -t GPU_NAMES < <(nvidia-smi --query-gpu=name --format=csv,noheader | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
if (( ${#GPU_NAMES[@]} != 1 )) || [[ ${GPU_NAMES[0]} != "$EXPECTED_GPU" ]]; then
  printf 'refusing: expected exactly one %s, observed: %s\n' \
    "$EXPECTED_GPU" "${GPU_NAMES[*]:-none}" >&2
  exit 2
fi

assert_gpu_idle() {
  local pids
  pids=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | sed '/^[[:space:]]*$/d')
  if [[ -n $pids ]]; then
    echo "refusing to share the GPU; foreign compute PIDs: $pids" >&2
    return 1
  fi
}
assert_gpu_idle

nvidia-smi --query-gpu=index,uuid,name,compute_cap,memory.total,driver_version,pstate,temperature.gpu,power.limit,clocks.max.graphics,clocks.max.memory \
  --format=csv,noheader,nounits >"$SESSION/metadata/gpu.csv"
nvidia-smi topo -m >"$SESSION/metadata/gpu-topology.txt"
uname -a >"$SESSION/metadata/uname.txt"
rustc -Vv >"$SESSION/metadata/rustc.txt"
cargo -V >"$SESSION/metadata/cargo.txt"
git rev-parse HEAD >"$SESSION/metadata/git-head.txt"
git status --short >"$SESSION/metadata/git-status.txt"
sha256sum suite/cuda/f4_gf2_echelon.cuh suite/cuda/f4_gf2_kernel.cu \
  suite/src/cryptanalysis/f4_gpu.rs suite/Cargo.lock \
  experiments/performance-saturation-20261101/gpu/analyze_gpu_aa_nsys.py \
  experiments/performance-saturation-20261101/gpu/run_gpu_aa_nsys.sh \
  ecc2k130/runner/codegen/install_nsys_tools.sh \
  >"$SESSION/metadata/source-sha256.txt"

RUNPOD_POD_ID_SAFE=$RUNPOD_POD_ID \
RUNPOD_MACHINE_ID_SAFE=${RUNPOD_MACHINE_ID:-} \
RUNPOD_CPU_COUNT_SAFE=${RUNPOD_CPU_COUNT:-} \
SESSION_ID_SAFE=$SESSION_ID \
SESSION_PATH_SAFE=$SESSION \
python3 - <<'PY'
import json, os, pathlib, platform
path = pathlib.Path(os.environ["SESSION_PATH_SAFE"]) / "host.json"
record = {
    "schema": "gpu-aa-host/v1",
    "session_id": os.environ["SESSION_ID_SAFE"],
    "provider": "runpod",
    "requested_cloud": "SECURE",
    "pod_id": os.environ["RUNPOD_POD_ID_SAFE"],
    "machine_id": os.environ["RUNPOD_MACHINE_ID_SAFE"] or None,
    "cpu_count": os.environ["RUNPOD_CPU_COUNT_SAFE"] or None,
    "platform": platform.platform(),
    "gpu_metadata": "metadata/gpu.csv",
    "gpu_topology": "metadata/gpu-topology.txt",
    "source_hashes": "metadata/source-sha256.txt",
}
with path.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, sort_keys=True, indent=2)
    stream.write("\n")
PY

echo "building the single A/A instrument" | tee "$SESSION/build.log"
(cd suite && CARGO_INCREMENTAL=0 cargo build --release --locked --example f4_matrix_bench) \
  >>"$SESSION/build.log" 2>&1
SOURCE_BIN="$REPO/suite/target/release/examples/f4_matrix_bench"
[[ -x $SOURCE_BIN ]] || { echo "build did not produce $SOURCE_BIN" >&2; exit 2; }
install -m 0755 "$SOURCE_BIN" "$BIN_DIR/control"
install -m 0755 "$SOURCE_BIN" "$BIN_DIR/current"
cmp -s "$BIN_DIR/control" "$BIN_DIR/current" || { echo "A/A binary copies differ" >&2; exit 2; }
control_sha=$(sha256sum "$BIN_DIR/control" | awk '{print $1}')
current_sha=$(sha256sum "$BIN_DIR/current" | awk '{print $1}')
[[ $control_sha = "$current_sha" ]] || { echo "A/A binary hashes differ" >&2; exit 2; }
printf 'control\t%s\ncurrent\t%s\n' "$control_sha" "$current_sha" >"$SESSION/binary-sha256.tsv"

SMI_QUERY=timestamp,index,uuid,pstate,temperature.gpu,utilization.gpu,utilization.memory,memory.used,power.draw,clocks.current.graphics,clocks.current.memory
start_smi() {
  local path=$1
  printf '%s\n' "$SMI_QUERY" >"$path"
  nvidia-smi --query-gpu="$SMI_QUERY" --format=csv,noheader,nounits -lms 200 \
    >>"$path" 2>"$path.stderr" &
  SMI_PID=$!
}
stop_smi() {
  if [[ -n ${SMI_PID:-} ]]; then
    kill "$SMI_PID" 2>/dev/null || true
    wait "$SMI_PID" 2>/dev/null || true
    unset SMI_PID
  fi
}

run_logged() {
  local telemetry=$1 log=$2 status=$3
  shift 3
  assert_gpu_idle || return 2
  start_smi "$telemetry"
  set +e
  "$@" >"$log" 2>&1
  local rc=$?
  set -e
  stop_smi
  printf '%s\n' "$rc" >"$status"
  return "$rc"
}

run_matrix() {
  local phase=$1 round_index=$2 role=$3 tag=$4 cell=$5 degree=$6 arm=$7
  local dir="$SESSION/raw/$phase/$(printf 'r%02d' "$round_index")/$tag"
  local prefix="$dir/$arm"
  mkdir -p "$dir"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$phase" "$round_index" "$tag" "$role" "$arm" "$cell:$degree" \
    >>"$SESSION/order.tsv"
  run_logged "$prefix.smi.csv" "$prefix.log" "$prefix.status" \
    env CUDA_VISIBLE_DEVICES=0 F4_F2_ECHELON=cuda F4_F2_ECHELON_VERBOSE=1 \
    "$BIN_DIR/$arm" --cell "$cell" --degree "$degree" --out "$prefix.json"
}

mapfile -t PLAN < <(python3 "$ANALYZER" plan --tsv)
printf 'phase\tround\tworkload\trole\tarm\tcell_degree\n' >"$SESSION/order.tsv"

run_round() {
  local phase=$1 round_index=$2 entry role tag cell degree
  local -a arms
  if (( round_index % 2 == 1 )); then
    arms=(control current)
  else
    arms=(current control)
  fi
  for entry in "${PLAN[@]}"; do
    IFS=$'\t' read -r role tag cell degree <<<"$entry"
    for arm in "${arms[@]}"; do
      if ! run_matrix "$phase" "$round_index" "$role" "$tag" "$cell" "$degree" "$arm"; then
        echo "matrix execution failed; preserving the row and refusing the phase: $phase r$round_index $tag $arm" >&2
        return 1
      fi
    done
  done
}

# One complete warmup per arm and cell.  It is correctness-gated before any
# measured row is admitted.
run_round warmup 0
python3 "$ANALYZER" gate --session "$SESSION" --phase warmup \
  --expected-gpu "$EXPECTED_GPU" | tee "$SESSION/warmup-gate.json"

# Six fresh-process rounds; each arm runs first in exactly three rounds.
for round_index in 1 2 3 4 5 6; do
  run_round measure "$round_index"
done
python3 "$ANALYZER" gate --session "$SESSION" --phase measure \
  --expected-gpu "$EXPECTED_GPU" | tee "$SESSION/measure-gate.json"

PRIMARY_TAG=k0n13m2d6
PRIMARY_CELL=0:13:2:1234
PRIMARY_DEGREE=6

run_nsys() {
  local arm=$1 dir="$SESSION/profiles/nsys/$arm" prefix
  mkdir -p "$dir"
  prefix="$dir/$PRIMARY_TAG"
  run_logged "$prefix.smi.csv" "$prefix.log" "$prefix.status" \
    "$NSYS_BIN" profile --trace=cuda,nvtx,osrt --sample=none --cpuctxsw=none \
    --force-overwrite=false --output="$prefix" \
    env CUDA_VISIBLE_DEVICES=0 F4_F2_ECHELON=cuda F4_F2_ECHELON_VERBOSE=1 \
    "$BIN_DIR/$arm" --cell "$PRIMARY_CELL" --degree "$PRIMARY_DEGREE" --out "$prefix.json"
  set +e
  "$NSYS_BIN" stats --report=cuda_gpu_kern_sum,cuda_api_sum --format=csv \
    "$prefix.nsys-rep" >"$prefix.stats.csv" 2>"$prefix.stats.stderr"
  local rc=$?
  set -e
  printf '%s\n' "$rc" >"$prefix.stats.status"
  return "$rc"
}

# Timeline and launch-gap diagnostics follow the sealed unprofiled A/A rows.
for arm in control current; do
  run_nsys "$arm"
done
python3 "$ANALYZER" gate --session "$SESSION" --phase nsys \
  --expected-gpu "$EXPECTED_GPU" | tee "$SESSION/nsys-gate.json"
python3 "$ANALYZER" analyze --session "$SESSION" \
  --expected-gpu "$EXPECTED_GPU" | tee "$SESSION/analysis-gate.json"

date -u +%Y-%m-%dT%H:%M:%SZ >"$SESSION/completed-at.txt"
echo "GPU A/A calibration complete: $SESSION"
