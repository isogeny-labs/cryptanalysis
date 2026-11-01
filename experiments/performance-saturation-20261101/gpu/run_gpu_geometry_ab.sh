#!/usr/bin/env bash
# Prospective one-variable CUDA F4 update-grid A/B with post-timing Nsys.
# Run only through a uniquely named Secure Runpod RTX 5090 HTTP-batch pod.
set -Eeuo pipefail
umask 077

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$SCRIPT_DIR/../../.." && pwd)
ANALYZER="$SCRIPT_DIR/analyze_gpu_geometry_ab.py"
EXPECTED_GPU="NVIDIA GeForce RTX 5090"
BASELINE_ORIGIN_COMMIT="7c712913b7e912494e87c35e854cfd0129bad89c"
CANDIDATE_COMMIT="59b6d7e17100d4d16db5d25c2762a5d5cf45ef4f"
CANDIDATE_TREE="af0ac7e239c0acaa063c1a1441d6fb374ebbf30b"
CANDIDATE_BUILD_ARCHIVE_SHA256="c70ce5a0061f39a3d506c4196e9db7b422a6d4de80dc161b6ff18f165f674740"
BASELINE_F4_SHA256="da8c53c757cac0dfd81d1f75bfc5845610b645338215e52710efa11d57783944"
CANDIDATE_F4_SHA256="77832323d4d5a2b6b49fa2ca26fe40de1a80c0a8e17a9bb1949081a30fa84953"
PRODUCTION_DIFF_SHA256="34bf0033dd2bbd14b30ef2eaacaceb2d3bf9869504fca043585b1c78b48e43d3"
F4_PATH="suite/src/cryptanalysis/f4_gpu.rs"
TOOLING_REF="refs/heads/codex/runpod-http-gpu-geometry-v10-20261101"
HISTORY_DEEPEN_COMMITS=32

OUT_ARG=${1:?usage: run_gpu_geometry_ab.sh REPOSITORY_RELATIVE_OUT_ROOT SESSION_ID PROTOCOL_SHA256}
SESSION_ID=${2:?missing session id}
PROTOCOL_SHA256=${3:?missing frozen protocol SHA-256}

if [[ ! $SESSION_ID =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$ ]]; then
  echo "unsafe session id: $SESSION_ID" >&2
  exit 2
fi
if [[ ! $PROTOCOL_SHA256 =~ ^[0-9a-f]{64}$ ]]; then
  echo "malformed protocol SHA-256" >&2
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

TEMP_ROOT=$(mktemp -d /tmp/cryptanalysis-gpu-geometry.XXXXXX)
case "$TEMP_ROOT" in
  /tmp/cryptanalysis-gpu-geometry.*) ;;
  *) echo "unexpected temporary path: $TEMP_ROOT" >&2; exit 2 ;;
esac
BIN_DIR="$TEMP_ROOT/bin"
SOURCE_DIR="$TEMP_ROOT/source"
TARGET_DIR="$TEMP_ROOT/target"
mkdir -p "$BIN_DIR" "$SOURCE_DIR/baseline" "$SOURCE_DIR/candidate" "$TARGET_DIR"

SMI_PID=
runner_status="$SESSION/runner-exit.status"
cleanup() {
  local rc=$?
  if [[ -n ${SMI_PID:-} ]]; then
    kill "$SMI_PID" 2>/dev/null || true
    wait "$SMI_PID" 2>/dev/null || true
  fi
  printf '%s\n' "$rc" >"$runner_status"
  case "$TEMP_ROOT" in
    /tmp/cryptanalysis-gpu-geometry.*) rm -rf -- "$TEMP_ROOT" ;;
  esac
  exit "$rc"
}
trap cleanup EXIT INT TERM

if [[ ${GPU_STUDY_SECURE:-0} != 1 ]]; then
  echo "refusing: GPU_STUDY_SECURE=1 must attest the registered Secure placement" >&2
  exit 2
fi
if [[ -z ${RUNPOD_POD_ID:-} ]]; then
  echo "refusing: RUNPOD_POD_ID is absent" >&2
  exit 2
fi

cd "$REPO"
# shellcheck source=../../../cloud/pod_env.sh
source cloud/pod_env.sh

for tool in cargo date diff git nvidia-smi python3 realpath rustc sha256sum sleep tar; do
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
  echo "missing nsys; use the registered pinned installer" >&2
  exit 2
}
"$NSYS_BIN" --version >"$SESSION/metadata/nsys-version.txt" 2>&1
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
    echo "refusing to share the GPU; compute PIDs: $pids" >&2
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
git rev-parse HEAD >"$SESSION/metadata/tooling-git-head.txt"
git status --short >"$SESSION/metadata/tooling-git-status.txt"
sha256sum experiments/performance-saturation-20261101/gpu/analyze_gpu_geometry_ab.py \
  experiments/performance-saturation-20261101/gpu/finalize_gpu_geometry_ab.py \
  experiments/performance-saturation-20261101/gpu/orchestrate_gpu_geometry_v10.py \
  experiments/performance-saturation-20261101/gpu/run_gpu_geometry_ab.sh \
  ecc2k130/runner/codegen/install_nsys_tools.sh \
  cloud/runpod_http_batch.py cloud/runpod_http_batch_server.py \
  >"$SESSION/metadata/tooling-sha256.txt"

RUNPOD_POD_ID_SAFE=$RUNPOD_POD_ID \
RUNPOD_MACHINE_ID_SAFE=${RUNPOD_MACHINE_ID:-} \
SESSION_ID_SAFE=$SESSION_ID \
SESSION_PATH_SAFE=$SESSION \
python3 - <<'PY'
import json, os, pathlib, platform
session = pathlib.Path(os.environ["SESSION_PATH_SAFE"])
cpu_model = None
for line in pathlib.Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
    if line.startswith("model name"):
        cpu_model = line.split(":", 1)[1].strip()
        break
memory_kib = None
for line in pathlib.Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
    if line.startswith("MemTotal:"):
        memory_kib = int(line.split()[1])
        break
record = {
    "schema": "gpu-geometry-host/v1",
    "session_id": os.environ["SESSION_ID_SAFE"],
    "provider": "runpod",
    "requested_cloud": "SECURE",
    "pod_id": os.environ["RUNPOD_POD_ID_SAFE"],
    "machine_id": os.environ["RUNPOD_MACHINE_ID_SAFE"] or None,
    "platform": platform.platform(),
    "kernel": platform.release(),
    "cpu_model": cpu_model,
    "logical_cpus": os.cpu_count(),
    "memory_bytes": None if memory_kib is None else memory_kib * 1024,
    "gpu_metadata": "metadata/gpu.csv",
    "gpu_topology": "metadata/gpu-topology.txt",
}
with (session / "host.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, sort_keys=True, indent=2)
    stream.write("\n")
PY

tooling_commit=$(git rev-parse HEAD)
git fetch -q --deepen="$HISTORY_DEEPEN_COMMITS" origin "$TOOLING_REF"
[[ $(git rev-parse FETCH_HEAD) = "$tooling_commit" ]] || {
  echo "tooling public ref moved between authenticated bootstrap and history deepening" >&2
  exit 2
}
git cat-file -e "$BASELINE_ORIGIN_COMMIT^{commit}"
git cat-file -e "$CANDIDATE_COMMIT^{commit}"
[[ $(git rev-parse "$CANDIDATE_COMMIT^{tree}") = "$CANDIDATE_TREE" ]] || {
  echo "candidate tree mismatch" >&2
  exit 2
}
baseline_f4=$(git show "$BASELINE_ORIGIN_COMMIT:$F4_PATH" | sha256sum | awk '{print $1}')
candidate_f4=$(git show "$CANDIDATE_COMMIT:$F4_PATH" | sha256sum | awk '{print $1}')
[[ $baseline_f4 = "$BASELINE_F4_SHA256" ]] || { echo "baseline F4 blob hash mismatch" >&2; exit 2; }
[[ $candidate_f4 = "$CANDIDATE_F4_SHA256" ]] || { echo "candidate F4 blob hash mismatch" >&2; exit 2; }
production_diff=$(git diff "$BASELINE_ORIGIN_COMMIT" "$CANDIDATE_COMMIT" -- "$F4_PATH" | sha256sum | awk '{print $1}')
[[ $production_diff = "$PRODUCTION_DIFF_SHA256" ]] || { echo "production diff hash mismatch" >&2; exit 2; }

# Archive the complete transitive build closure, not multi-gigabyte historical
# experiment data that Cargo cannot read for this target.
git archive --format=tar --output="$TEMP_ROOT/candidate.tar" "$CANDIDATE_COMMIT" -- \
  suite bindings/rust include src
candidate_archive_sha=$(sha256sum "$TEMP_ROOT/candidate.tar" | awk '{print $1}')
[[ $candidate_archive_sha = "$CANDIDATE_BUILD_ARCHIVE_SHA256" ]] || {
  echo "candidate build-closure archive hash mismatch" >&2
  exit 2
}
tar -xf "$TEMP_ROOT/candidate.tar" -C "$SOURCE_DIR/baseline"
tar -xf "$TEMP_ROOT/candidate.tar" -C "$SOURCE_DIR/candidate"
git show "$BASELINE_ORIGIN_COMMIT:$F4_PATH" >"$SOURCE_DIR/baseline/$F4_PATH"

mapfile -t SOURCE_DIFFS < <(diff -qr "$SOURCE_DIR/baseline" "$SOURCE_DIR/candidate" || true)
if (( ${#SOURCE_DIFFS[@]} != 1 )) || [[ ${SOURCE_DIFFS[0]} != *"$F4_PATH"* ]]; then
  printf 'arm source trees differ outside the registered production path:\n%s\n' "${SOURCE_DIFFS[*]}" >&2
  exit 2
fi

BASELINE_ORIGIN_COMMIT_SAFE=$BASELINE_ORIGIN_COMMIT \
CANDIDATE_COMMIT_SAFE=$CANDIDATE_COMMIT \
CANDIDATE_TREE_SAFE=$CANDIDATE_TREE \
BASELINE_F4_SHA256_SAFE=$BASELINE_F4_SHA256 \
CANDIDATE_F4_SHA256_SAFE=$CANDIDATE_F4_SHA256 \
PRODUCTION_DIFF_SHA256_SAFE=$PRODUCTION_DIFF_SHA256 \
CANDIDATE_ARCHIVE_SHA256_SAFE=$candidate_archive_sha \
F4_PATH_SAFE=$F4_PATH \
TOOLING_REF_SAFE=$TOOLING_REF \
HISTORY_DEEPEN_COMMITS_SAFE=$HISTORY_DEEPEN_COMMITS \
SESSION_PATH_SAFE=$SESSION \
python3 - <<'PY'
import json, os, pathlib
value = {
    "schema": "gpu-geometry-source-identities/v1",
    "baseline_origin_commit": os.environ["BASELINE_ORIGIN_COMMIT_SAFE"],
    "candidate_commit": os.environ["CANDIDATE_COMMIT_SAFE"],
    "candidate_tree": os.environ["CANDIDATE_TREE_SAFE"],
    "candidate_archive_sha256": os.environ["CANDIDATE_ARCHIVE_SHA256_SAFE"],
    "production_path": os.environ["F4_PATH_SAFE"],
    "baseline_f4_sha256": os.environ["BASELINE_F4_SHA256_SAFE"],
    "candidate_f4_sha256": os.environ["CANDIDATE_F4_SHA256_SAFE"],
    "production_diff_sha256": os.environ["PRODUCTION_DIFF_SHA256_SAFE"],
    "only_production_path_differs": True,
    "tooling_ref": os.environ["TOOLING_REF_SAFE"],
    "history_deepen_commits": int(os.environ["HISTORY_DEEPEN_COMMITS_SAFE"]),
    "construction": "two copies of the candidate commit build-closure archive (suite, bindings/rust, include, src); baseline overlays only the registered baseline F4 file",
}
path = pathlib.Path(os.environ["SESSION_PATH_SAFE"]) / "source-identities.json"
with path.open("x", encoding="utf-8") as stream:
    json.dump(value, stream, sort_keys=True, indent=2)
    stream.write("\n")
PY

echo "building the two isolated one-factor instruments" | tee "$SESSION/build.log"
for arm in baseline candidate; do
  (
    cd "$SOURCE_DIR/$arm/suite"
    CARGO_INCREMENTAL=0 CARGO_TARGET_DIR="$TARGET_DIR/$arm" \
      cargo build --release --locked --example f4_matrix_bench
  ) >>"$SESSION/build.log" 2>&1
  source_bin="$TARGET_DIR/$arm/release/examples/f4_matrix_bench"
  [[ -x $source_bin ]] || { echo "build did not produce $source_bin" >&2; exit 2; }
  install -m 0755 "$source_bin" "$BIN_DIR/$arm"
done
baseline_bin_sha=$(sha256sum "$BIN_DIR/baseline" | awk '{print $1}')
candidate_bin_sha=$(sha256sum "$BIN_DIR/candidate" | awk '{print $1}')
[[ $baseline_bin_sha != "$candidate_bin_sha" ]] || { echo "one-factor binaries are unexpectedly identical" >&2; exit 2; }
install -m 0755 "$BIN_DIR/baseline" "$BIN_DIR/baseline-aa"
baseline_aa_bin_sha=$(sha256sum "$BIN_DIR/baseline-aa" | awk '{print $1}')
[[ $baseline_aa_bin_sha = "$baseline_bin_sha" ]] || { echo "A/A binary differs from baseline" >&2; exit 2; }
printf 'baseline\t%s\nbaseline-aa\t%s\ncandidate\t%s\n' \
  "$baseline_bin_sha" "$baseline_aa_bin_sha" "$candidate_bin_sha" \
  >"$SESSION/binary-sha256.tsv"

# Keep compilation pressure out of the first registered warmup snapshot.
date -u +%Y-%m-%dT%H:%M:%SZ >"$SESSION/metadata/post-build-settle-started-at.txt"
sleep 30
date -u +%Y-%m-%dT%H:%M:%SZ >"$SESSION/metadata/post-build-settle-finished-at.txt"

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
    SMI_PID=
  fi
}

run_logged() {
  local prefix=$1
  shift
  assert_gpu_idle
  python3 "$ANALYZER" snapshot-isolation --out "$prefix.isolation-before.json"
  date -u +%Y-%m-%dT%H:%M:%SZ >"$prefix.started-at"
  start_smi "$prefix.smi.csv"
  set +e
  "$@" >"$prefix.log" 2>&1
  local rc=$?
  set -e
  stop_smi
  date -u +%Y-%m-%dT%H:%M:%SZ >"$prefix.finished-at"
  printf '%s\n' "$rc" >"$prefix.status"
  assert_gpu_idle
  python3 "$ANALYZER" snapshot-isolation --out "$prefix.isolation-after.json"
  return "$rc"
}

mapfile -t PLAN < <(python3 "$ANALYZER" plan --tsv)
printf 'phase\tround\tworkload\trole\tarm\tcell_degree\n' >"$SESSION/order.tsv"

run_matrix() {
  local phase=$1 round_index=$2 role=$3 tag=$4 cell=$5 degree=$6 arm=$7
  local dir="$SESSION/raw/$phase/$(printf 'r%02d' "$round_index")/$tag"
  local prefix="$dir/$arm"
  mkdir -p "$dir"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$phase" "$round_index" "$tag" "$role" "$arm" "$cell:$degree" \
    >>"$SESSION/order.tsv"
  run_logged "$prefix" \
    env CUDA_VISIBLE_DEVICES=0 F4_F2_ECHELON=cuda F4_F2_ECHELON_VERBOSE=1 \
    "$BIN_DIR/$arm" --cell "$cell" --degree "$degree" --out "$prefix.json"
}

run_round() {
  local phase=$1 round_index=$2 entry role tag cell degree
  local -a arms
  case "$round_index" in
    0) arms=(baseline baseline-aa candidate) ;;
    1) arms=(baseline candidate baseline-aa) ;;
    2) arms=(baseline-aa candidate baseline) ;;
    3) arms=(candidate baseline baseline-aa) ;;
    4) arms=(baseline-aa baseline candidate) ;;
    5) arms=(baseline baseline-aa candidate) ;;
    6) arms=(candidate baseline-aa baseline) ;;
    *) echo "unregistered round index: $round_index" >&2; return 2 ;;
  esac
  for entry in "${PLAN[@]}"; do
    IFS=$'\t' read -r role tag cell degree <<<"$entry"
    for arm in "${arms[@]}"; do
      if ! run_matrix "$phase" "$round_index" "$role" "$tag" "$cell" "$degree" "$arm"; then
        echo "matrix execution failed: $phase r$round_index $tag $arm" >&2
        return 1
      fi
    done
  done
}

run_round warmup 0
python3 "$ANALYZER" gate --session "$SESSION" --phase warmup --expected-gpu "$EXPECTED_GPU" \
  | tee "$SESSION/warmup-gate.json"

for round_index in 1 2 3 4 5 6; do
  run_round measure "$round_index"
done
python3 "$ANALYZER" gate --session "$SESSION" --phase measure --expected-gpu "$EXPECTED_GPU" \
  | tee "$SESSION/measure-gate.json"

PRIMARY_TAG=k0n13m2d6
PRIMARY_CELL=0:13:2:1234
PRIMARY_DEGREE=6
run_nsys() {
  local arm=$1
  local dir="$SESSION/profiles/nsys/$arm"
  local prefix="$dir/$PRIMARY_TAG"
  mkdir -p "$dir"
  run_logged "$prefix" \
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

for arm in baseline candidate; do
  run_nsys "$arm"
done
python3 "$ANALYZER" gate --session "$SESSION" --phase nsys --expected-gpu "$EXPECTED_GPU" \
  | tee "$SESSION/nsys-gate.json"
python3 "$ANALYZER" analyze --session "$SESSION" --expected-gpu "$EXPECTED_GPU" \
  --protocol-sha256 "$PROTOCOL_SHA256" | tee "$SESSION/analysis-gate.json"

date -u +%Y-%m-%dT%H:%M:%SZ >"$SESSION/completed-at.txt"
echo "GPU geometry A/B complete: $SESSION"
