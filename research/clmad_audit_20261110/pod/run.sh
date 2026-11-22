#!/usr/bin/env bash
# Runs on the pod after the bundle is unpacked at /work/bundle.  Writes
# /work/results/.  Never edits anything under the bundle except build/.
set -u
cd /work/bundle || exit 9
EXP=research/clmad_audit_20261110
OUT=/work/results
B=$EXP/build
mkdir -p "$OUT" "$B"
ARCH="-gencode arch=compute_120,code=sm_120"
log() { echo "[$(date -u +%H:%M:%S)] $*"; }

{
  echo "## date"; date -u
  echo "## nvidia-smi"; nvidia-smi || true
  nvidia-smi --query-gpu=name,uuid,driver_version,compute_cap,clocks.max.sm,clocks.sm,clocks.mem,power.limit,pcie.link.gen.current --format=csv || true
  echo "## nvcc"; nvcc --version
  echo "## ptxas"; ptxas --version
  echo "## cuobjdump"; cuobjdump --version
  echo "## gcc"; gcc --version | head -1
  echo "## os"; cat /etc/os-release | head -3
  echo "## cpu"; grep -m1 "model name" /proc/cpuinfo; nproc
  echo "## clock lock attempt"
  nvidia-smi -lgc 0,9999 2>&1 | head -2 || true
  echo "## bundle sha256"; cat /work/bundle.sha256 2>/dev/null
} > "$OUT/env.txt" 2>&1

# ---- Q1: repro matrix -------------------------------------------------------
: > "$OUT/repro_summary.tsv"
echo -e "binary\tN\tptxas_opt\tcodegen\tvariant\texit\tclmad_sass\tfirst_line" >> "$OUT/repro_summary.tsv"
run_repro() { # name N opt codegen variant extra-defs...
  local name=$1 n=$2 opt=$3 cg=$4 var=$5; shift 5
  local gen
  if [ "$cg" = sass ]; then gen="$ARCH"; else gen="-gencode arch=compute_120,code=compute_120"; fi
  nvcc -O3 -std=c++17 $gen -Xptxas -O$opt -DN=$n "$@" $EXP/src/repro.cu -o "$B/$name" > "$OUT/build_$name.log" 2>&1
  local bexit=$?
  local sass=na
  if [ $bexit -ne 0 ]; then echo -e "$name\t$n\t$opt\t$cg\t$var\tbuild_fail\tna\t$(head -1 "$OUT/build_$name.log")" >> "$OUT/repro_summary.tsv"; return; fi
  if [ "$cg" = sass ]; then sass=$(cuobjdump -sass "$B/$name" 2>/dev/null | grep -c "CLMAD"); fi
  "$B/$name" > "$OUT/run_$name.txt" 2>&1
  local rexit=$?
  echo -e "$name\t$n\t$opt\t$cg\t$var\t$rexit\t$sass\t$(head -1 "$OUT/run_$name.txt")" >> "$OUT/repro_summary.tsv"
}
for n in 14 15 16 18 19; do
  for o in 3 2 1 0; do
    run_repro "repro_N${n}_O${o}" $n $o sass karatsuba
  done
done
run_repro "repro_N14_O3_ptxjit" 14 3 ptx karatsuba
run_repro "repro_N14_O3_schoolbook" 14 3 sass schoolbook -DSCHOOLBOOK
run_repro "repro_N64_O3_square" 64 3 sass square -DSQUARE
run_repro "repro_N14_O3_seed2" 14 3 sass karatsuba_seed2
# a second seed for the headline binary, run through the same binary:
"$B/repro_N14_O3" 0x1234567 > "$OUT/run_repro_N14_O3_altseed.txt" 2>&1; echo "altseed exit=$?" >> "$OUT/run_repro_N14_O3_altseed.txt"
log "repro done"

# ---- Q2: ecc2k130 tests -----------------------------------------------------
PACKED="PACKED_SINGLE_PRODUCT=1 PACKED_CACHE_DENOM=1 PACKED_BY_VALUE=1 PACKED_PERM_SIGMA=3 PACKED_POLY_CHAIN=1 PACKED_UNROLL_INV=1 PACKED_PAIR_PRODUCTS=1 PACKED_POLY_STATE=1 PACKED_DIRECT_REDUCE=1 PACKED_GENERATED_PRODUCT=1 PACKED_CLMAD=1 PACKED_STATE_TILE=256 PACKED_WEIGHTED_PREFIX=2 PACKED_COMPACT_STATE=1 PACKED_SHARED_SIGMA=1"
( cd ecc2k130/runner && make test-clmad test-clmad-square ) > "$OUT/ecc2k130_host_tests.log" 2>&1
echo "host_tests_exit=$?" >> "$OUT/ecc2k130_host_tests.log"
( cd ecc2k130/runner && make test-packed-cuda ARCH="$ARCH" $PACKED ) > "$OUT/ecc2k130_test_packed_cuda.log" 2>&1
echo "test_packed_cuda_exit=$?" >> "$OUT/ecc2k130_test_packed_cuda.log"
( cd ecc2k130/runner && make -n test-packed-cuda ARCH="$ARCH" $PACKED ) > "$OUT/ecc2k130_test_packed_cuda.cmd" 2>&1
log "ecc2k130 tests done"

# ---- Q3: timing ---------------------------------------------------------------
nvcc -O3 -std=c++17 $ARCH $EXP/src/clmad_timing.cu -o "$B/timing" > "$OUT/build_timing.log" 2>&1
if [ $? -eq 0 ]; then
  cuobjdump -sass "$B/timing" > "$OUT/timing.sass" 2>/dev/null
  "$B/timing" --geometry latency --reps 100 --blocks 1 --threads 32 --raw 1 --out "$OUT/timing_latency.jsonl" 2> "$OUT/timing_latency.err"
  echo "latency_exit=$?" >> "$OUT/timing_latency.err"
  "$B/timing" --geometry occupancy --reps 50 --blocks-per-sm 2 --threads 256 --raw 0 --seed 20261111 --out "$OUT/timing_occupancy.jsonl" 2> "$OUT/timing_occupancy.err"
  echo "occupancy_exit=$?" >> "$OUT/timing_occupancy.err"
fi
nvidia-smi --query-gpu=clocks.sm,clocks.mem,temperature.gpu,power.draw --format=csv > "$OUT/env_after.txt" 2>&1
log "timing done"
cd /work && tar -cJf /work/results.tar.xz results && sha256sum results.tar.xz > results.sha256
echo done
