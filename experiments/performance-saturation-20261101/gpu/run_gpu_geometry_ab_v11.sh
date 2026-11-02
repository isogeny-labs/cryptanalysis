#!/usr/bin/env bash
# Prospective one-variable CUDA F4 update-grid A/B with post-timing Nsys.
# Run only through a uniquely named Secure Runpod RTX 5090 HTTP-batch pod.
set -Eeuo pipefail
umask 077
# The runner shell itself performs source and binary identity checks.  Close
# its lookup path before the first external command so an inherited shim cannot
# forge those checks.
export PATH=/usr/bin:/bin

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$SCRIPT_DIR/../../.." && pwd)
ANALYZER="$SCRIPT_DIR/analyze_gpu_geometry_ab_v11.py"
EXPECTED_GPU="NVIDIA GeForce RTX 5090"
BASELINE_ORIGIN_COMMIT="7c712913b7e912494e87c35e854cfd0129bad89c"
CANDIDATE_COMMIT="59b6d7e17100d4d16db5d25c2762a5d5cf45ef4f"
CANDIDATE_TREE="af0ac7e239c0acaa063c1a1441d6fb374ebbf30b"
CANDIDATE_BUILD_ARCHIVE_SHA256="554dcaacb7ff1fcfb27f4b49bb60b2d03ac9201978091c5e516fff356d1f9b8d"
BASELINE_F4_SHA256="da8c53c757cac0dfd81d1f75bfc5845610b645338215e52710efa11d57783944"
CANDIDATE_F4_SHA256="77832323d4d5a2b6b49fa2ca26fe40de1a80c0a8e17a9bb1949081a30fa84953"
PRODUCTION_DIFF_SHA256="34bf0033dd2bbd14b30ef2eaacaceb2d3bf9869504fca043585b1c78b48e43d3"
F4_PATH="suite/src/cryptanalysis/f4_gpu.rs"
TOOLING_REF="refs/heads/codex/runpod-http-gpu-geometry-v11-20261101"
HISTORY_DEEPEN_COMMITS=64
NVRTC_WHEEL_URL="https://files.pythonhosted.org/packages/b8/85/e4af82cc9202023862090bfca4ea827d533329e925c758f0cde964cb54b7/nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-manylinux2010_x86_64.manylinux_2_12_x86_64.whl"
NVRTC_WHEEL_SHA256="210cf05005a447e29214e9ce50851e83fc5f4358df8b453155d5e1918094dcb4"
NVRTC_WHEEL_BYTES=89568129
NVRTC_LIBRARY_SHA256="7c67c6b51ea0e0279634cebd676ff7efda1674806444520c84430ad5c35fe625"
NVRTC_LIBRARY_BYTES=106244480
NVRTC_BUILTINS_SHA256="6507cf33450cfb22970c2c1e7aa8e7c0a33e39d864720277b05f61a92791e2e8"
NVRTC_BUILTINS_BYTES=7202760
NSYS_PACKAGE="nsight-systems-2026.3.2"
NSYS_PACKAGE_VERSION="2026.3.2.476-263238834031v0"
NSYS_DEB_URL="https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/nsight-systems-2026.3.2_2026.3.2.476-1_amd64.deb"
NSYS_DEB_SHA256="e9bf0ff9c613ff5545095a4177676a9579cb666e78c8621c3792f3559e2c1690"
NSYS_DEB_BYTES=448261416
NSYS_BINARY_RELATIVE="opt/nvidia/nsight-systems/2026.3.2/target-linux-x64/nsys"
NSYS_BINARY_CONTRACT="<remote-task-root>/nsys-package/$NSYS_BINARY_RELATIVE"
NSYS_BINARY_SHA256="68a5fb843322bda1b090900a0297b9d5bee43daf8b870a809a6f8aa93059ae16"
NSYS_BINARY_BYTES=87282816
NSYS_VERSION_REGISTERED="NVIDIA Nsight Systems version 2026.3.2.476-263238834031v0"

OUT_ARG=${1:?usage: run_gpu_geometry_ab_v11.sh REPOSITORY_RELATIVE_OUT_ROOT SESSION_ID PROTOCOL_SHA256 PREFLIGHT_RECEIPT_SHA256}
SESSION_ID=${2:?missing session id}
PROTOCOL_SHA256=${3:?missing frozen protocol SHA-256}
PREFLIGHT_RECEIPT_SHA256=${4:?missing preflight receipt SHA-256}

if [[ ! $SESSION_ID =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$ ]]; then
  echo "unsafe session id: $SESSION_ID" >&2
  exit 2
fi
if [[ ! $PROTOCOL_SHA256 =~ ^[0-9a-f]{64}$ ]]; then
  echo "malformed protocol SHA-256" >&2
  exit 2
fi
if [[ ! $PREFLIGHT_RECEIPT_SHA256 =~ ^[0-9a-f]{64}$ ]]; then
  echo "malformed preflight receipt SHA-256" >&2
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

TEMP_ROOT=$(mktemp -d /tmp/cryptanalysis-gpu-geometry-v11.XXXXXX)
case "$TEMP_ROOT" in
  /tmp/cryptanalysis-gpu-geometry-v11.*) ;;
  *) echo "unexpected temporary path: $TEMP_ROOT" >&2; exit 2 ;;
esac
BIN_DIR="$TEMP_ROOT/bin"
BUILD_ROOT="$TEMP_ROOT/build-root"
MEASURE_HOME="$TEMP_ROOT/measurement-home"
MEASURE_TMP="$TEMP_ROOT/measurement-tmp"
STRICT_PATH="/usr/bin:/bin"
BUILD_SYSTEM_PATH="/usr/bin:/bin"
mkdir -p "$BIN_DIR" "$MEASURE_HOME" "$MEASURE_TMP"

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
    /tmp/cryptanalysis-gpu-geometry-v11.*) rm -rf -- "$TEMP_ROOT" ;;
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
validate_loader_path() {
  local value=$1 entry normalized
  local -a entries
  [[ $value != :* && $value != *: && $value != *::* ]] || return 1
  IFS=: read -r -a entries <<<"$value"
  for entry in "${entries[@]}"; do
    [[ -n $entry && $entry = /* && $entry != *'/../'* && $entry != */.. && $entry != *'//'* ]] || return 1
    normalized=$(realpath -m -- "$entry")
    [[ $normalized = "$entry" && -d $entry ]] || return 1
    case "$entry/" in
      /usr/local/nvidia/*|/usr/local/cuda/*|/usr/lib/*|/lib/*) ;;
      *) return 1 ;;
    esac
  done
}
if [[ -n ${LD_LIBRARY_PATH:-} ]] && ! validate_loader_path "$LD_LIBRARY_PATH"; then
  echo "inherited LD_LIBRARY_PATH is outside the frozen trusted absolute roots" >&2
  exit 2
fi
SYSTEM_ENV=(
  /usr/bin/env -i
  "PATH=$STRICT_PATH" "HOME=$MEASURE_HOME" "TMPDIR=$MEASURE_TMP"
  "LANG=C" "LC_ALL=C" "TZ=UTC"
)
if [[ -n ${LD_LIBRARY_PATH:-} ]]; then
  SYSTEM_ENV+=("LD_LIBRARY_PATH=$LD_LIBRARY_PATH")
fi
BUILD_GATE_ENV=(
  /usr/bin/env -i
  "PATH=$BUILD_SYSTEM_PATH" "HOME=$MEASURE_HOME" "TMPDIR=$MEASURE_TMP"
  "LANG=C" "LC_ALL=C" "TZ=UTC"
)
PREFLIGHT_ENV=(
  /usr/bin/env -i
  "PATH=/usr/bin:/bin" "HOME=$MEASURE_HOME" "TMPDIR=$MEASURE_TMP"
  "LANG=C" "LC_ALL=C" "TZ=UTC"
)
for network_key in ALL_PROXY HTTPS_PROXY HTTP_PROXY NO_PROXY SSL_CERT_FILE CURL_CA_BUNDLE; do
  if [[ -v $network_key ]]; then
    BUILD_GATE_ENV+=("$network_key=${!network_key}")
    PREFLIGHT_ENV+=("$network_key=${!network_key}")
  fi
done

for tool in date git nvidia-smi realpath sha256sum sleep; do
  command -v "$tool" >/dev/null || { echo "missing required tool: $tool" >&2; exit 2; }
done
[[ -x /usr/bin/python3 ]] || { echo "missing exact /usr/bin/python3" >&2; exit 2; }

mapfile -t GPU_NAMES < <("${SYSTEM_ENV[@]}" nvidia-smi --query-gpu=name --format=csv,noheader | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
if (( ${#GPU_NAMES[@]} != 1 )) || [[ ${GPU_NAMES[0]} != "$EXPECTED_GPU" ]]; then
  printf 'refusing: expected exactly one %s, observed: %s\n' \
    "$EXPECTED_GPU" "${GPU_NAMES[*]:-none}" >&2
  exit 2
fi

assert_gpu_idle() {
  local pids
  pids=$("${SYSTEM_ENV[@]}" nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | sed '/^[[:space:]]*$/d')
  if [[ -n $pids ]]; then
    echo "refusing to share the GPU; compute PIDs: $pids" >&2
    return 1
  fi
}
assert_gpu_idle

"${SYSTEM_ENV[@]}" nvidia-smi --query-gpu=index,uuid,name,compute_cap,memory.total,driver_version,pstate,temperature.gpu,power.limit,clocks.max.graphics,clocks.max.memory \
  --format=csv,noheader,nounits >"$SESSION/metadata/gpu.csv"
"${SYSTEM_ENV[@]}" nvidia-smi topo -m >"$SESSION/metadata/gpu-topology.txt"
"${SYSTEM_ENV[@]}" uname -a >"$SESSION/metadata/uname.txt"
"${PREFLIGHT_ENV[@]}" git rev-parse HEAD >"$SESSION/metadata/tooling-git-head.txt"
"${PREFLIGHT_ENV[@]}" git status --short >"$SESSION/metadata/tooling-git-status.txt"
sha256sum experiments/performance-saturation-20261101/gpu/analyze_gpu_geometry_ab_v11.py \
  experiments/performance-saturation-20261101/gpu/finalize_gpu_geometry_ab_v11.py \
  experiments/performance-saturation-20261101/gpu/orchestrate_gpu_geometry_v11.py \
  experiments/performance-saturation-20261101/gpu/preflight_gpu_geometry_v11.py \
  experiments/performance-saturation-20261101/gpu/run_gpu_geometry_ab_v11.sh \
  ecc2k130/runner/codegen/extract_nsys_tools_v11.sh \
  cloud/runpod_http_batch.py cloud/runpod_http_batch_server.py \
  cloud/runpod_pod.py cloud/ship.py cloud/tree.py cloud/pod_env.sh cloud/job_runner.sh \
  >"$SESSION/metadata/tooling-sha256.txt"

"${SYSTEM_ENV[@]}" \
RUNPOD_POD_ID_SAFE=$RUNPOD_POD_ID \
RUNPOD_MACHINE_ID_SAFE=${RUNPOD_MACHINE_ID:-} \
SESSION_ID_SAFE=$SESSION_ID \
SESSION_PATH_SAFE=$SESSION \
/usr/bin/python3 -I -S -B - <<'PY'
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

tooling_commit=$("${PREFLIGHT_ENV[@]}" git rev-parse HEAD)
"${PREFLIGHT_ENV[@]}" git fetch -q --deepen="$HISTORY_DEEPEN_COMMITS" origin "$TOOLING_REF"
[[ $("${PREFLIGHT_ENV[@]}" git rev-parse FETCH_HEAD) = "$tooling_commit" ]] || {
  echo "tooling public ref moved between authenticated bootstrap and history deepening" >&2
  exit 2
}
"${PREFLIGHT_ENV[@]}" git cat-file -e "$BASELINE_ORIGIN_COMMIT^{commit}"
"${PREFLIGHT_ENV[@]}" git cat-file -e "$CANDIDATE_COMMIT^{commit}"
[[ $("${PREFLIGHT_ENV[@]}" git rev-parse "$CANDIDATE_COMMIT^{tree}") = "$CANDIDATE_TREE" ]] || {
  echo "candidate tree mismatch" >&2
  exit 2
}
baseline_f4=$("${PREFLIGHT_ENV[@]}" git show "$BASELINE_ORIGIN_COMMIT:$F4_PATH" | sha256sum | awk '{print $1}')
candidate_f4=$("${PREFLIGHT_ENV[@]}" git show "$CANDIDATE_COMMIT:$F4_PATH" | sha256sum | awk '{print $1}')
[[ $baseline_f4 = "$BASELINE_F4_SHA256" ]] || { echo "baseline F4 blob hash mismatch" >&2; exit 2; }
[[ $candidate_f4 = "$CANDIDATE_F4_SHA256" ]] || { echo "candidate F4 blob hash mismatch" >&2; exit 2; }
production_diff=$("${PREFLIGHT_ENV[@]}" git diff "$BASELINE_ORIGIN_COMMIT" "$CANDIDATE_COMMIT" -- "$F4_PATH" | sha256sum | awk '{print $1}')
[[ $production_diff = "$PRODUCTION_DIFF_SHA256" ]] || { echo "production diff hash mismatch" >&2; exit 2; }

# Reuse the same hash-bound environment-closed builder that gated allocation.
# It recreates the full six-root archive, fetches locked dependencies only in
# its network allowlist, and performs both builds offline with exact env keys.
"${PREFLIGHT_ENV[@]}" /usr/bin/python3 -I -S -B \
  "$REPO/experiments/performance-saturation-20261101/gpu/preflight_gpu_geometry_v11.py" \
  prepare-remote --repo "$REPO" --workspace "$BUILD_ROOT" \
  --run-id "$SESSION_ID" --protocol-sha256 "$PROTOCOL_SHA256" \
  --out "$SESSION/metadata/remote-build-preflight.json"
candidate_archive_sha=$(sha256sum "$BUILD_ROOT/candidate.tar" | awk '{print $1}')
[[ $candidate_archive_sha = "$CANDIDATE_BUILD_ARCHIVE_SHA256" ]] || {
  echo "candidate build-closure archive hash mismatch after remote preflight" >&2
  exit 2
}

"${SYSTEM_ENV[@]}" \
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
PREFLIGHT_RECEIPT_SHA256_SAFE=$PREFLIGHT_RECEIPT_SHA256 \
REMOTE_BUILD_PREFLIGHT_SHA256_SAFE=$(sha256sum "$SESSION/metadata/remote-build-preflight.json" | awk '{print $1}') \
SESSION_PATH_SAFE=$SESSION \
/usr/bin/python3 -I -S -B - <<'PY'
import json, os, pathlib
value = {
    "schema": "gpu-geometry-source-identities/v1",
    "baseline_origin_commit": os.environ["BASELINE_ORIGIN_COMMIT_SAFE"],
    "candidate_commit": os.environ["CANDIDATE_COMMIT_SAFE"],
    "candidate_tree": os.environ["CANDIDATE_TREE_SAFE"],
    "candidate_archive_sha256": os.environ["CANDIDATE_ARCHIVE_SHA256_SAFE"],
    "archive_paths": ["suite", "bindings/rust", "include", "src", "cuda", "challenges"],
    "production_path": os.environ["F4_PATH_SAFE"],
    "baseline_f4_sha256": os.environ["BASELINE_F4_SHA256_SAFE"],
    "candidate_f4_sha256": os.environ["CANDIDATE_F4_SHA256_SAFE"],
    "production_diff_sha256": os.environ["PRODUCTION_DIFF_SHA256_SAFE"],
    "only_production_path_differs": True,
    "tooling_ref": os.environ["TOOLING_REF_SAFE"],
    "history_deepen_commits": int(os.environ["HISTORY_DEEPEN_COMMITS_SAFE"]),
    "preflight_receipt_sha256": os.environ["PREFLIGHT_RECEIPT_SHA256_SAFE"],
    "remote_build_preflight_sha256": os.environ["REMOTE_BUILD_PREFLIGHT_SHA256_SAFE"],
    "construction": "two copies of the candidate commit build-closure archive (suite, bindings/rust, include, src, cuda, challenges); baseline overlays only the registered baseline F4 file",
}
path = pathlib.Path(os.environ["SESSION_PATH_SAFE"]) / "source-identities.json"
with path.open("x", encoding="utf-8") as stream:
    json.dump(value, stream, sort_keys=True, indent=2)
    stream.write("\n")
PY

"${SYSTEM_ENV[@]}" /usr/bin/python3 -I -S -B - \
  "$SESSION/metadata/remote-build-preflight.json" >"$SESSION/build.log" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
print("environment-closed remote builds:")
for item in value["builds"]:
    print(item["arm"], item["returncode"], item["binary_sha256"], item["log_sha256"])
PY
for arm in baseline candidate; do
  source_bin="$BUILD_ROOT/target/$arm/release/examples/f4_matrix_bench"
  [[ -x $source_bin ]] || { echo "remote preflight did not produce $source_bin" >&2; exit 2; }
  install -m 0755 "$source_bin" "$BIN_DIR/$arm"
done
baseline_bin_sha=$(sha256sum "$BIN_DIR/baseline" | awk '{print $1}')
candidate_bin_sha=$(sha256sum "$BIN_DIR/candidate" | awk '{print $1}')
[[ $baseline_bin_sha != "$candidate_bin_sha" ]] || { echo "one-factor binaries are unexpectedly identical" >&2; exit 2; }
install -m 0755 "$BUILD_ROOT/baseline-aa" "$BIN_DIR/baseline-aa"
baseline_aa_bin_sha=$(sha256sum "$BIN_DIR/baseline-aa" | awk '{print $1}')
[[ $baseline_aa_bin_sha = "$baseline_bin_sha" ]] || { echo "A/A binary differs from baseline" >&2; exit 2; }
printf 'baseline\t%s\nbaseline-aa\t%s\ncandidate\t%s\n' \
  "$baseline_bin_sha" "$baseline_aa_bin_sha" "$candidate_bin_sha" \
  >"$SESSION/binary-sha256.tsv"

# Only after both closure builds pass, materialize the exact registered NVRTC
# wheel without executing pip/package code.  The benchmark receives only the
# extracted, hash-bound library path.
NVRTC_ROOT="$TEMP_ROOT/nvrtc-wheel"
"${BUILD_GATE_ENV[@]}" \
  NVRTC_URL_SAFE=$NVRTC_WHEEL_URL \
  NVRTC_WHEEL_SHA256_SAFE=$NVRTC_WHEEL_SHA256 \
  NVRTC_WHEEL_BYTES_SAFE=$NVRTC_WHEEL_BYTES \
  NVRTC_LIBRARY_SHA256_SAFE=$NVRTC_LIBRARY_SHA256 \
  NVRTC_LIBRARY_BYTES_SAFE=$NVRTC_LIBRARY_BYTES \
  NVRTC_BUILTINS_SHA256_SAFE=$NVRTC_BUILTINS_SHA256 \
  NVRTC_BUILTINS_BYTES_SAFE=$NVRTC_BUILTINS_BYTES \
  NVRTC_ROOT_SAFE=$NVRTC_ROOT \
  NVRTC_RECEIPT_SAFE=$SESSION/metadata/nvrtc-install.json \
  /usr/bin/python3 -I -S -B - <<'PY'
import ctypes, hashlib, io, json, os, pathlib, urllib.request, zipfile

url = os.environ["NVRTC_URL_SAFE"]
wheel_expected = os.environ["NVRTC_WHEEL_SHA256_SAFE"]
wheel_bytes_expected = int(os.environ["NVRTC_WHEEL_BYTES_SAFE"])
library_expected = os.environ["NVRTC_LIBRARY_SHA256_SAFE"]
library_bytes_expected = int(os.environ["NVRTC_LIBRARY_BYTES_SAFE"])
builtins_expected = os.environ["NVRTC_BUILTINS_SHA256_SAFE"]
builtins_bytes_expected = int(os.environ["NVRTC_BUILTINS_BYTES_SAFE"])
root = pathlib.Path(os.environ["NVRTC_ROOT_SAFE"])
receipt = pathlib.Path(os.environ["NVRTC_RECEIPT_SAFE"])
with urllib.request.urlopen(url, timeout=300) as response:
    wheel = response.read(128 * 1024 * 1024 + 1)
if (len(wheel) != wheel_bytes_expected
        or hashlib.sha256(wheel).hexdigest() != wheel_expected):
    raise SystemExit("NVRTC wheel identity mismatch")
member = "nvidia/cuda_nvrtc/lib/libnvrtc.so.12"
builtins_member = "nvidia/cuda_nvrtc/lib/libnvrtc-builtins.so.12.9"
with zipfile.ZipFile(io.BytesIO(wheel)) as archive:
    names = archive.namelist()
    if names.count(member) != 1 or names.count(builtins_member) != 1:
        raise SystemExit("NVRTC wheel lacks unique registered libraries")
    library = archive.read(member)
    builtins = archive.read(builtins_member)
if (len(library) != library_bytes_expected
        or hashlib.sha256(library).hexdigest() != library_expected):
    raise SystemExit("NVRTC library identity mismatch")
if (len(builtins) != builtins_bytes_expected
        or hashlib.sha256(builtins).hexdigest() != builtins_expected):
    raise SystemExit("NVRTC builtins identity mismatch")
root.mkdir(parents=True, exist_ok=False)
path = root / "libnvrtc.so.12"
with path.open("xb") as stream:
    stream.write(library)
builtins_path = root / "libnvrtc-builtins.so.12.9"
with builtins_path.open("xb") as stream:
    stream.write(builtins)

# Loading the main library is insufficient: NVRTC opens the versioned builtins
# sibling only while compiling.  This positive probe makes adjacency part of
# the admission gate before any profiling tools are installed.
nvrtc = ctypes.CDLL(str(path))
program = ctypes.c_void_p()
nvrtc.nvrtcCreateProgram.argtypes = [
    ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p, ctypes.c_char_p,
    ctypes.c_int, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p),
]
nvrtc.nvrtcCreateProgram.restype = ctypes.c_int
nvrtc.nvrtcCompileProgram.argtypes = [
    ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_char_p),
]
nvrtc.nvrtcCompileProgram.restype = ctypes.c_int
nvrtc.nvrtcDestroyProgram.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
nvrtc.nvrtcDestroyProgram.restype = ctypes.c_int
source = b'extern "C" __global__ void gpu_v11_probe() {}'
rc = nvrtc.nvrtcCreateProgram(
    ctypes.byref(program), source, b"gpu-v11-probe.cu", 0, None, None,
)
if rc != 0:
    raise SystemExit(f"NVRTC create probe failed: {rc}")
option = ctypes.c_char_p(b"--gpu-architecture=compute_120")
try:
    rc = nvrtc.nvrtcCompileProgram(program, 1, ctypes.pointer(option))
finally:
    destroy_rc = nvrtc.nvrtcDestroyProgram(ctypes.byref(program))
if rc != 0 or destroy_rc != 0:
    raise SystemExit(f"NVRTC compile/destroy probe failed: {rc}/{destroy_rc}")
record = {
    "schema": "gpu-geometry-nvrtc-install/v1",
    "package": "nvidia-cuda-nvrtc-cu12",
    "version": "12.9.86",
    "wheel_url": url,
    "wheel_sha256": wheel_expected,
    "wheel_bytes": len(wheel),
    "libraries": [
        {"wheel_member": member,
         "path": "<remote-task-root>/nvrtc-wheel/libnvrtc.so.12",
         "sha256": library_expected, "bytes": len(library)},
        {"wheel_member": builtins_member,
         "path": "<remote-task-root>/nvrtc-wheel/libnvrtc-builtins.so.12.9",
         "sha256": builtins_expected, "bytes": len(builtins)},
    ],
    "compile_probe": {"architecture": "compute_120", "returncode": 0},
    "python_package_code_executed": False,
    "native_compile_probe_executed": True,
}
with receipt.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, sort_keys=True, indent=2)
    stream.write("\n")
PY
CA_NVRTC_LIB="$NVRTC_ROOT/libnvrtc.so.12"
[[ $(sha256sum "$CA_NVRTC_LIB" | awk '{print $1}') = "$NVRTC_LIBRARY_SHA256" ]] || {
  echo "materialized NVRTC library identity mismatch" >&2
  exit 2
}
NVRTC_BUILTINS_LIB="$NVRTC_ROOT/libnvrtc-builtins.so.12.9"
[[ $(sha256sum "$NVRTC_BUILTINS_LIB" | awk '{print $1}') = "$NVRTC_BUILTINS_SHA256" ]] || {
  echo "materialized NVRTC builtins identity mismatch" >&2
  exit 2
}
NVRTC_SHA256=$NVRTC_LIBRARY_SHA256

# The exact closure and NVRTC library are ready before profiler extraction.
NSYS_PACKAGE_ROOT="$TEMP_ROOT/nsys-package"
"${BUILD_GATE_ENV[@]}" /usr/bin/bash "$REPO/ecc2k130/runner/codegen/extract_nsys_tools_v11.sh" \
  "$NSYS_PACKAGE_ROOT" \
  >"$SESSION/metadata/nsys-install.log" 2>&1
NSYS_BIN=$(realpath -e -- "$NSYS_PACKAGE_ROOT/$NSYS_BINARY_RELATIVE") || {
  echo "missing exact nsys binary after registered package extraction" >&2
  exit 2
}
[[ $NSYS_BIN = "$NSYS_PACKAGE_ROOT/$NSYS_BINARY_RELATIVE" && -x $NSYS_BIN ]] || {
  echo "nsys resolved outside the fresh extracted package root" >&2
  exit 2
}
"${SYSTEM_ENV[@]}" "$NSYS_BIN" --version >"$SESSION/metadata/nsys-version.txt" 2>&1
[[ $(tr -d '\r\n' <"$SESSION/metadata/nsys-version.txt") = "$NSYS_VERSION_REGISTERED" ]] || {
  echo "nsys runtime version differs from the registered value" >&2
  exit 2
}
NSYS_SHA256=$(sha256sum "$NSYS_BIN" | awk '{print $1}')
NSYS_BYTES=$(stat -c %s "$NSYS_BIN")
[[ $NSYS_SHA256 = "$NSYS_BINARY_SHA256" && $NSYS_BYTES = "$NSYS_BINARY_BYTES" ]] || {
  echo "extracted nsys binary content differs from the registered artifact" >&2
  exit 2
}
"${SYSTEM_ENV[@]}" \
  NSYS_PACKAGE_SAFE=$NSYS_PACKAGE \
  NSYS_PACKAGE_VERSION_SAFE=$NSYS_PACKAGE_VERSION \
  NSYS_DEB_URL_SAFE=$NSYS_DEB_URL \
  NSYS_DEB_SHA256_SAFE=$NSYS_DEB_SHA256 \
  NSYS_DEB_BYTES_SAFE=$NSYS_DEB_BYTES \
  NSYS_PACKAGE_ROOT_SAFE=$NSYS_PACKAGE_ROOT \
  NSYS_BINARY_CONTRACT_SAFE=$NSYS_BINARY_CONTRACT \
  NSYS_BINARY_SAFE=$NSYS_BIN \
  NSYS_SHA256_SAFE=$NSYS_SHA256 \
  NSYS_BYTES_SAFE=$NSYS_BYTES \
  NSYS_VERSION_SAFE=$NSYS_VERSION_REGISTERED \
  NSYS_EXTRACTOR_SHA256_SAFE=$(sha256sum "$REPO/ecc2k130/runner/codegen/extract_nsys_tools_v11.sh" | awk '{print $1}') \
  NSYS_RECEIPT_SAFE=$SESSION/metadata/nsys-install.json \
  /usr/bin/python3 -I -S -B - <<'PY'
import json, os, pathlib
record = {
    "schema": "gpu-geometry-nsys-install/v1",
    "package": os.environ["NSYS_PACKAGE_SAFE"],
    "package_version": os.environ["NSYS_PACKAGE_VERSION_SAFE"],
    "package_deb_url": os.environ["NSYS_DEB_URL_SAFE"],
    "package_deb_sha256": os.environ["NSYS_DEB_SHA256_SAFE"],
    "package_deb_bytes": int(os.environ["NSYS_DEB_BYTES_SAFE"]),
    "package_control": {
        "Package": os.environ["NSYS_PACKAGE_SAFE"],
        "Version": os.environ["NSYS_PACKAGE_VERSION_SAFE"],
        "Architecture": "amd64",
    },
    "extraction_root": "<remote-task-root>/nsys-package",
    "extraction_root_realpath": os.environ["NSYS_PACKAGE_ROOT_SAFE"],
    "binary_path": os.environ["NSYS_BINARY_CONTRACT_SAFE"],
    "binary_realpath": os.environ["NSYS_BINARY_SAFE"],
    "binary_sha256": os.environ["NSYS_SHA256_SAFE"],
    "binary_bytes": int(os.environ["NSYS_BYTES_SAFE"]),
    "version_output": os.environ["NSYS_VERSION_SAFE"],
    "installed": False,
    "maintainer_scripts_executed": False,
    "system_package_manager_mutation": False,
    "dependency_source": "digest-pinned image plus exact extracted deb; missing dependencies fail closed",
    "extractor_path": "ecc2k130/runner/codegen/extract_nsys_tools_v11.sh",
    "extractor_sha256": os.environ["NSYS_EXTRACTOR_SHA256_SAFE"],
}
path = pathlib.Path(os.environ["NSYS_RECEIPT_SAFE"])
with path.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, sort_keys=True, indent=2)
    stream.write("\n")
PY
set +e
"${SYSTEM_ENV[@]}" "$NSYS_BIN" stats --help-reports >"$SESSION/metadata/nsys-reports.txt" 2>&1
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

MEASURE_LD_LIBRARY_PATH="$NVRTC_ROOT${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
MEASURE_ENV=(
  /usr/bin/env -i
  "PATH=$STRICT_PATH" "HOME=$MEASURE_HOME" "TMPDIR=$MEASURE_TMP"
  "LANG=C" "LC_ALL=C" "TZ=UTC"
  "CUDA_VISIBLE_DEVICES=0" "F4_F2_ECHELON=cuda" "F4_F2_ECHELON_VERBOSE=1"
  "CA_NVRTC_LIB=$CA_NVRTC_LIB"
  "LD_LIBRARY_PATH=$MEASURE_LD_LIBRARY_PATH"
)
"${SYSTEM_ENV[@]}" \
  INHERITED_LD_LIBRARY_PATH_SAFE=${LD_LIBRARY_PATH:-} \
  MEASURE_LD_LIBRARY_PATH_SAFE=$MEASURE_LD_LIBRARY_PATH \
  NVRTC_ROOT_SAFE=$NVRTC_ROOT \
  NVRTC_PATH_SAFE=$CA_NVRTC_LIB \
  NVRTC_SHA256_SAFE=$NVRTC_SHA256 \
  NVRTC_BUILTINS_PATH_SAFE=$NVRTC_BUILTINS_LIB \
  NVRTC_BUILTINS_SHA256_SAFE=$NVRTC_BUILTINS_SHA256 \
  MEASURE_HOME_SAFE=$MEASURE_HOME \
  MEASURE_TMP_SAFE=$MEASURE_TMP \
  SESSION_PATH_SAFE=$SESSION \
  /usr/bin/python3 -I -S -B - <<'PY'
import hashlib, json, os, pathlib
inherited_loader = os.environ["INHERITED_LD_LIBRARY_PATH_SAFE"]
measurement_loader = os.environ["MEASURE_LD_LIBRARY_PATH_SAFE"]
nvrtc_root = os.environ["NVRTC_ROOT_SAFE"]
fixed = {
    "PATH": "/usr/bin:/bin",
    "HOME": "<remote-task-root>/measurement-home",
    "TMPDIR": "<remote-task-root>/measurement-tmp",
    "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
    "CUDA_VISIBLE_DEVICES": "0", "F4_F2_ECHELON": "cuda",
    "F4_F2_ECHELON_VERBOSE": "1",
    "CA_NVRTC_LIB": "<remote-task-root>/nvrtc-wheel/libnvrtc.so.12",
}
keys = sorted([*fixed, "LD_LIBRARY_PATH"])
value = {
    "schema": "gpu-geometry-measurement-environment/v1",
    "construction": "env -i exact allowlist for every timed binary; env -i system subset for analyzer and Nsys",
    "measurement_fixed": fixed,
    "measurement_exact_keys": keys,
    "system_exact_keys": sorted(["PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ", *(["LD_LIBRARY_PATH"] if inherited_loader else [])]),
    "inherited_loader_path_present": bool(inherited_loader),
    "inherited_loader_path_entries": inherited_loader.split(":") if inherited_loader else [],
    "inherited_loader_path_value_sha256": hashlib.sha256(inherited_loader.encode()).hexdigest() if inherited_loader else None,
    "measurement_loader_first": "<remote-task-root>/nvrtc-wheel",
    "measurement_loader_value_sha256": hashlib.sha256(measurement_loader.encode()).hexdigest(),
    "nvrtc_root_realpath": nvrtc_root,
    "nvrtc_library_realpath": os.environ["NVRTC_PATH_SAFE"],
    "nvrtc_library_sha256": os.environ["NVRTC_SHA256_SAFE"],
    "nvrtc_builtins_realpath": os.environ["NVRTC_BUILTINS_PATH_SAFE"],
    "nvrtc_builtins_sha256": os.environ["NVRTC_BUILTINS_SHA256_SAFE"],
    "forbidden_absent": [
        "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CFLAGS", "CXXFLAGS", "CPPFLAGS",
        "LDFLAGS", "LD_PRELOAD", "RUSTC_WRAPPER", "RAYON_NUM_THREADS",
    ],
    "forbidden_prefixes_absent": ["CARGO_PROFILE_", "F4_ except the two exact fixed keys"],
}
path = pathlib.Path(os.environ["SESSION_PATH_SAFE"]) / "metadata/measurement-environment.json"
with path.open("x", encoding="utf-8") as stream:
    json.dump(value, stream, sort_keys=True, indent=2)
    stream.write("\n")
PY

# Keep compilation pressure out of the first registered warmup snapshot.
date -u +%Y-%m-%dT%H:%M:%SZ >"$SESSION/metadata/post-build-settle-started-at.txt"
sleep 30
date -u +%Y-%m-%dT%H:%M:%SZ >"$SESSION/metadata/post-build-settle-finished-at.txt"

SMI_QUERY=timestamp,index,uuid,pstate,temperature.gpu,utilization.gpu,utilization.memory,memory.used,power.draw,clocks.current.graphics,clocks.current.memory
start_smi() {
  local path=$1
  printf '%s\n' "$SMI_QUERY" >"$path"
  "${SYSTEM_ENV[@]}" nvidia-smi --query-gpu="$SMI_QUERY" --format=csv,noheader,nounits -lms 200 \
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
  "${SYSTEM_ENV[@]}" /usr/bin/python3 -I -S -B "$ANALYZER" snapshot-isolation --out "$prefix.isolation-before.json"
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
  "${SYSTEM_ENV[@]}" /usr/bin/python3 -I -S -B "$ANALYZER" snapshot-isolation --out "$prefix.isolation-after.json"
  return "$rc"
}

mapfile -t PLAN < <("${SYSTEM_ENV[@]}" /usr/bin/python3 -I -S -B "$ANALYZER" plan --tsv)
printf 'phase\tround\tworkload\trole\tarm\tcell_degree\n' >"$SESSION/order.tsv"

run_matrix() {
  local phase=$1 round_index=$2 role=$3 tag=$4 cell=$5 degree=$6 arm=$7
  local dir="$SESSION/raw/$phase/$(printf 'r%02d' "$round_index")/$tag"
  local prefix="$dir/$arm"
  mkdir -p "$dir"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$phase" "$round_index" "$tag" "$role" "$arm" "$cell:$degree" \
    >>"$SESSION/order.tsv"
  run_logged "$prefix" \
    "${MEASURE_ENV[@]}" \
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
"${SYSTEM_ENV[@]}" /usr/bin/python3 -I -S -B "$ANALYZER" gate --session "$SESSION" --phase warmup --expected-gpu "$EXPECTED_GPU" \
  | tee "$SESSION/warmup-gate.json"

for round_index in 1 2 3 4 5 6; do
  run_round measure "$round_index"
done
"${SYSTEM_ENV[@]}" /usr/bin/python3 -I -S -B "$ANALYZER" gate --session "$SESSION" --phase measure --expected-gpu "$EXPECTED_GPU" \
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
    "${SYSTEM_ENV[@]}" "$NSYS_BIN" profile --trace=cuda,nvtx,osrt --sample=none --cpuctxsw=none \
    --force-overwrite=false --output="$prefix" \
    "${MEASURE_ENV[@]}" \
    "$BIN_DIR/$arm" --cell "$PRIMARY_CELL" --degree "$PRIMARY_DEGREE" --out "$prefix.json"
  set +e
  "${SYSTEM_ENV[@]}" "$NSYS_BIN" stats --report=cuda_gpu_kern_sum,cuda_api_sum --format=csv \
    "$prefix.nsys-rep" >"$prefix.stats.csv" 2>"$prefix.stats.stderr"
  local rc=$?
  set -e
  printf '%s\n' "$rc" >"$prefix.stats.status"
  return "$rc"
}

for arm in baseline candidate; do
  run_nsys "$arm"
done
[[ $(sha256sum "$NSYS_BIN" | awk '{print $1}') = "$NSYS_SHA256" ]] || {
  echo "nsys binary drifted during the registered profiles" >&2
  exit 2
}
[[ $(stat -c %s "$NSYS_BIN") = "$NSYS_BINARY_BYTES" ]] || {
  echo "nsys binary byte length drifted during the registered profiles" >&2
  exit 2
}
printf '%s  %s\n' "$NSYS_SHA256" "$NSYS_BINARY_CONTRACT" \
  >"$SESSION/metadata/nsys-after.sha256"
[[ $(sha256sum "$CA_NVRTC_LIB" | awk '{print $1}') = "$NVRTC_SHA256" ]] || {
  echo "NVRTC library drifted during the registered executions" >&2
  exit 2
}
[[ $(sha256sum "$NVRTC_BUILTINS_LIB" | awk '{print $1}') = "$NVRTC_BUILTINS_SHA256" ]] || {
  echo "NVRTC builtins drifted during the registered executions" >&2
  exit 2
}
printf '%s  libnvrtc.so.12\n%s  libnvrtc-builtins.so.12.9\n' \
  "$NVRTC_SHA256" "$NVRTC_BUILTINS_SHA256" >"$SESSION/metadata/nvrtc-after.sha256"
"${SYSTEM_ENV[@]}" /usr/bin/python3 -I -S -B "$ANALYZER" gate --session "$SESSION" --phase nsys --expected-gpu "$EXPECTED_GPU" \
  | tee "$SESSION/nsys-gate.json"
"${SYSTEM_ENV[@]}" /usr/bin/python3 -I -S -B "$ANALYZER" analyze --session "$SESSION" --expected-gpu "$EXPECTED_GPU" \
  --protocol-sha256 "$PROTOCOL_SHA256" | tee "$SESSION/analysis-gate.json"

date -u +%Y-%m-%dT%H:%M:%SZ >"$SESSION/completed-at.txt"
echo "GPU geometry A/B complete: $SESSION"
