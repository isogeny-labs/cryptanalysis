#!/usr/bin/env bash
# Root provisions/fetches/deletes the one bounded pod. This script makes no API calls.
set -u -o pipefail
STUDY=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
OUT=${1:-"$STUDY/remote/run-0"}
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT";; esac
if [[ -e "$OUT/started.utc" ]]; then
  printf 'Refusing to overwrite an existing run: %s\n' "$OUT" >&2
  exit 2
fi
mkdir -p "$OUT"
date -u +%FT%TZ > "$OUT/started.utc"
ECC="$STUDY/source/tree/ecc2k130"
BUILD="$OUT/build"
INGEST="$OUT/ingest-control"
GPU="$BUILD/ec2k-gpu"
record() {
  local label=$1
  shift
  printf '%q ' "$@" > "$OUT/$label.command"
  printf '\n' >> "$OUT/$label.command"
  set +e
  /usr/bin/time -v -o "$OUT/$label.resources" "$@" > "$OUT/$label.stdout" 2> "$OUT/$label.stderr"
  local rc=$?
  printf '%s\n' "$rc" > "$OUT/$label.exit"
  set -e
  return "$rc"
}
hardware() {
  uname -a > "$OUT/uname.txt"
  lscpu > "$OUT/lscpu.txt"
  cat /proc/meminfo > "$OUT/meminfo.txt"
  cat /proc/self/status > "$OUT/process-status.txt"
  for file in cpu.max cpu.stat memory.max memory.events; do
    if [[ -r "/sys/fs/cgroup/$file" ]]; then cat "/sys/fs/cgroup/$file" > "$OUT/cgroup-$file.before"; fi
  done
  nvidia-smi -q > "$OUT/nvidia-smi.txt" 2> "$OUT/nvidia-smi.stderr"
  cc --version > "$OUT/cc-version.txt"
  c++ --version > "$OUT/cxx-version.txt"
  (cd "$STUDY" && sha256sum -c source/ecc.sha256) > "$OUT/ecc-source-verification.txt"
  (cd "$STUDY" && sha256sum -c launch-v2.sha256) > "$OUT/launch-source-verification.txt"
}
ecc_pipeline() {
  set -e
  for exe in make cc c++ pip unzip timeout sha256sum nvidia-smi; do command -v "$exe" > /dev/null; done
  test -x /usr/bin/time
  record ecc-host-test make -C "$ECC" test -j4 "BUILD=$BUILD"
  record ingest-build c++ -O2 -std=c++17 -DECC_WALK_TABLE=0 "-I$ECC/src" "$STUDY/ingest_control_v2.cpp" "$BUILD/model.o" -o "$INGEST"
  record ingest-fixture "$INGEST" fixture "$OUT/fixture"
  record ingest-fixture-check "$INGEST" check "$OUT/fixture.32" "$OUT/fixture.64" 53180 60 8 10000
  record cuda-fetch "$ECC/scripts/fetch_cuda.sh" "$OUT/cuda"
  local nvcc="$OUT/cuda/bin/nvcc"
  "$nvcc" --version > "$OUT/nvcc-version.txt"
  grep -q 'V13.3.73' "$OUT/nvcc-version.txt"
  sha256sum "$OUT/cuda/wheels/"*.whl > "$OUT/cuda-wheels.sha256"
  # Compile only for the exact physical device; no inherited ARCH guess.
  local cap arch
  cap=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | tr -d '.[:space:]')
  case "$cap" in 80|86|89|90|100|120) ;; *) printf 'Unsupported CUDA capability: %s\n' "$cap" >&2; return 3;; esac
  arch="-gencode arch=compute_$cap,code=sm_$cap"
  printf '%s\n' "$arch" > "$OUT/cuda-architecture.txt"
  record ecc-gpu-build make -C "$ECC" gpu -j4 "BUILD=$BUILD" "NVCC=$nvcc" "ARCH=$arch"
  sha256sum "$GPU" "$INGEST" > "$OUT/native-binaries.sha256"
  record ecc-devices "$GPU" devices
  record ecc-native-check "$GPU" check --rounds 64 --kat "$ECC/tests/campaign-kat.hex"
  record ecc-correctness "$GPU" walk --run-id 53180 --dp-weight 46 --threads 256 --steps 96 --launches 8 --verify 3 --dp-cap 1048576 --dp-file "$OUT/control.32" --dp-file64 "$OUT/control.64"
  record ecc-correctness-summary "$INGEST" summary "$OUT/ecc-correctness.stdout" 3 3 0
  record ecc-correctness-ingestion "$INGEST" check "$OUT/control.32" "$OUT/control.64" 53180 46 8 512
  record ecc-health "$GPU" health --seconds 10 --warmup 2 --window 2 --threads 256
  # Deterministic checkpoint boundary: same eight launches, split 4 + 4.
  record ecc-restart-first "$GPU" walk --run-id 53180 --dp-weight 46 --threads 256 --steps 96 --launches 4 --dp-cap 1048576 --dp-file "$OUT/restarted.32" --dp-file64 "$OUT/restarted.64" --checkpoint "$OUT/control.ck"
  cp "$OUT/control.ck" "$OUT/control.first.ck"
  record ecc-restart-first-header "$INGEST" header "$OUT/control.first.ck" 53180 46
  record ecc-restart-second "$GPU" walk --run-id 53180 --dp-weight 46 --threads 256 --steps 96 --launches 4 --dp-cap 1048576 --dp-file "$OUT/restarted.32" --dp-file64 "$OUT/restarted.64" --checkpoint "$OUT/control.ck"
  grep -q 'resumed from' "$OUT/ecc-restart-second.stdout"
  record ecc-restart-equality "$INGEST" compare "$OUT/control.32" "$OUT/restarted.32"
  record ecc-restart-ingestion "$INGEST" check "$OUT/restarted.32" "$OUT/restarted.64" 53180 46 8 512
  record ecc-tamper-fixture "$INGEST" tamper "$OUT/control.64" "$OUT/control.tampered.64"
  if record ecc-tamper-rejection "$INGEST" check "$OUT/control.32" "$OUT/control.tampered.64" 53180 46 8 512; then
    printf 'Tampered control was accepted\n' >&2; return 4
  else
    test "$(cat "$OUT/ecc-tamper-rejection.exit")" = 1
  fi
  for sample in 1 2 3; do
    record "ecc-bench-$sample" "$GPU" bench --steps 1024 --launches 64
    record "ecc-bench-$sample-summary" "$INGEST" summary "$OUT/ecc-bench-$sample.stdout" 0 0 0
  done
  record merge-build cc -O2 -std=c11 "$STUDY/source/tree/fpga/model/ecc2k130.c" "$STUDY/source/tree/fpga/host/ec2k_tool.c" -o "$OUT/ec2k-merge"
  for phase in first second; do
    if record "ecc-challenge-$phase" timeout --signal=TERM --kill-after=60 180 "$GPU" walk --run-id 53181 --dp-weight 32 --max-iters 4294967296 --steps 4096 --dp-cap 1048576 --checkpoint-every 30 --dp-file "$OUT/challenge.32" --dp-file64 "$OUT/challenge.64" --checkpoint "$OUT/challenge.ck"; then
      :
    else
      test "$(cat "$OUT/ecc-challenge-$phase.exit")" = 124
    fi
    record "ecc-challenge-$phase-summary" "$INGEST" summary "$OUT/ecc-challenge-$phase.stdout" 0 1 1
    cp "$OUT/challenge.ck" "$OUT/challenge.$phase.ck"
    record "ecc-challenge-$phase-header" "$INGEST" header "$OUT/challenge.$phase.ck" 53181 32
    record "ecc-challenge-$phase-ingestion" "$INGEST" check "$OUT/challenge.32" "$OUT/challenge.64" 53181 32 8 512
  done
  grep -q 'resumed from' "$OUT/ecc-challenge-second.stdout"
  record challenge-checkpoint-advance "$INGEST" advance "$OUT/challenge.first.ck" "$OUT/challenge.second.ck" 53181 32
  record challenge-ingest "$OUT/ec2k-merge" merge "$OUT/challenge.32"
  record challenge-duplicate-ingest "$OUT/ec2k-merge" merge "$OUT/challenge.32" "$OUT/challenge.32"
  record challenge-duplicate-gate "$INGEST" merge-check "$OUT/challenge-ingest.stdout" "$OUT/challenge-duplicate-ingest.stdout"
  sha256sum "$OUT/"*.32 "$OUT/"*.64 "$OUT/"*.ck > "$OUT/records-checkpoints.sha256"
}
negation_pipeline() {
  set -e
  record negation-build cc -O3 -std=c11 "$STUDY/source/negation-rho.c" -lm -o "$OUT/negation-rho"
  local params=(--p 2381327587 --a 2074994603 --b 2059223808 --N 2381318239 --gx 2294151594 --gy 816999591 --seed 1 --r 20 --dpbits 12 --budget-mult 64 --walk-cap-mult 64)
  for rule in none det reselect; do
    record "negation-$rule" timeout --signal=TERM --kill-after=5 120 "$OUT/negation-rho" run-vw "${params[@]}" --mode 1 --escape "$rule"
  done
  record negation-baseline timeout --signal=TERM --kill-after=5 120 "$OUT/negation-rho" run-vw "${params[@]}" --mode 0 --escape none
}
set +e
(set -e; hardware)
hardware_rc=$?
printf '%s\n' "$hardware_rc" > "$OUT/hardware.exit"
if [[ $hardware_rc = 0 ]]; then
  (set -e; ecc_pipeline)
  ecc_rc=$?
else
  ecc_rc=3
fi
printf '%s\n' "$ecc_rc" > "$OUT/ecc-pipeline.exit"
(set -e; negation_pipeline)
negation_rc=$?
printf '%s\n' "$negation_rc" > "$OUT/negation-pipeline.exit"
if [[ -x "$STUDY/frontier_highram.sh" ]]; then
  (set -e; "$STUDY/frontier_highram.sh" "$OUT/frontier") > "$OUT/frontier-launch.stdout" 2> "$OUT/frontier-launch.stderr"
  frontier_rc=$?
else
  frontier_rc=3
  printf 'Frontier launch script absent\n' > "$OUT/frontier-launch.stderr"
fi
printf '%s\n' "$frontier_rc" > "$OUT/frontier-pipeline.exit"
for file in cpu.stat memory.events; do
  if [[ -r "/sys/fs/cgroup/$file" ]]; then cat "/sys/fs/cgroup/$file" > "$OUT/cgroup-$file.after"; fi
done
date -u +%FT%TZ > "$OUT/finished.utc"
printf '{"ecc_exit":%s,"negation_exit":%s,"frontier_exit":%s,"challenge_solution_claimed":false,"campaign_seed_range_reserved":false}\n' "$ecc_rc" "$negation_rc" "$frontier_rc" > "$OUT/execution-status.json"
test "$ecc_rc" = 0 && test "$negation_rc" = 0 && test "$frontier_rc" = 0
