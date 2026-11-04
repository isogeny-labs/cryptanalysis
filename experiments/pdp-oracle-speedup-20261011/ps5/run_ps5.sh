#!/bin/sh
# run_ps5.sh - PS-5 on a CPU-only host: build the kernel's emulation from
# PS-3's recorded program and replay the PS-0 corpus through it.
#
#   run_ps5.sh manifest            hardware/toolchain manifest -> raw/manifest.json
#   run_ps5.sh build  [MODE]       unpack + hash-check programs, emit, build (MODE plain|model; default plain)
#                                  $PS5_RUNGS picks the rungs (default "8 9 10 11 12")
#   run_ps5.sh selftest L [REPS] [MODE]   truth tables, every wire, the function (raw/selftest_lL[_model].jsonl)
#   run_ps5.sh parity   L [THREADS] [MODE]   corpus replay (raw/parity_lL[_model].jsonl)
#   run_ps5.sh sanitize            ASan+UBSan build of the drivers at l = 8 against the existing emulation object (raw/sanitizers_l8.txt)
#   run_ps5.sh nvcc   L            compile the CUDA kernel (needs $NVCC; no device is used)
#
# Heavy steps are meant to be run as
#   python3 <crypto>/tools/isolated_bench.py busy --wait -- experiments/pdp-oracle-speedup-20261011/ps5/run_ps5.sh ...
# $OUT (default /tmp/pdp_ps5_build) holds the build.  $PDP_SPEEDUP names the PS-3 binary of the `crypto`
# repository (default /tmp/ps3_bin/pdp_speedup, SHA-256 c40434d6...a6c1) that exports the programs: they are
# regenerated and hash-checked, not committed (data-file rule of AGENTS.md).
# Nothing here starts a device, a pod or a cloud job.
set -eu
HERE=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH='' cd -- "$HERE/../../.." && pwd)
OUT=${OUT:-/tmp/pdp_ps5_build}
RAW=$HERE/raw
mkdir -p "$OUT" "$RAW"

# SHA-256 of each program's uncompressed bytes, recorded by PS-2 (ps2_scalar/README.md section 5).
prog_sha() {
    case $1 in
        8) echo f34227cade15eb2b3c18852ac5de2a25a4e62a1566c5976ac6e3c6a012bdca98 ;;
        9) echo 5faf5360ff9d9fb20ff418166c80d51f8731b5bf56149d14535491cd53461a6e ;;
        10) echo c2a413f9f136c0a3c585920fa4ee40c5d67d39a260576b153db36e2dda0ac43b ;;
        11) echo 099679633c4d2f0c11f4e8b6024b6aa3d1a8703e59980f712593e90fb7065954 ;;
        12) echo a8bec32c3185d52f68cbd313dbff3840febc9d8c4ef99a826ab521dfc3862b9a ;;
        # l = 13 is timing-only in the plan and was not frozen by PS-2: this hash is first recorded by PS-5
        # (raw/export_check.txt), from the same binary.
        13) echo a494467d8b006e2fc06df2b6385c75baf75979a016d4d8b69ab0858b555d9538 ;;
    esac
}
# PS-0's digests for run 1 of rung L (baseline_v1/digests.txt, copied as expected_digests_ps0.txt).
digest_of() { # L which(verdicts|roots)
    awk -v l="l=$1" -v w="digest_$2" '$1=="run=1" && $2==l { for (i=1;i<=NF;i++) if ($i==w) print $(i+1) }' \
        "$HERE/expected_digests_ps0.txt"
}

PDP_SPEEDUP=${PDP_SPEEDUP:-/tmp/ps3_bin/pdp_speedup}
PS3_BIN_SHA=c40434d66da31bf619d79a3c27ee617e19b36a061067fac075d409391734a6c1

# export_program L: write $OUT/prog/pdp_slp_lL_b8.slp(.json) with the PS-3 binary and check its hash against the recorded one
export_program() {
    l=$1
    mkdir -p "$OUT/prog"
    [ -x "$PDP_SPEEDUP" ] || { echo "PDP_SPEEDUP=$PDP_SPEEDUP is not an executable (the PS-3 pdp_speedup binary)"; exit 1; }
    got_bin=$(sha256sum "$PDP_SPEEDUP" | cut -d' ' -f1)
    [ "$got_bin" = "$PS3_BIN_SHA" ] || echo "note: $PDP_SPEEDUP has SHA-256 $got_bin, not the PS-3 binary's $PS3_BIN_SHA; the program hash decides"
    "$PDP_SPEEDUP" export-program --l "$l" --tasks 8 --out "$OUT/prog/pdp_slp_l${l}_b8.slp" > "$OUT/prog/export_l$l.json"
    got=$(sha256sum "$OUT/prog/pdp_slp_l${l}_b8.slp" | cut -d' ' -f1)
    [ "$got" = "$(prog_sha "$l")" ] || { echo "l=$l: program hash $got differs from the recorded $(prog_sha "$l")"; exit 1; }
    cmp -s "$OUT/prog/pdp_slp_l${l}_b8.slp.json" "$HERE/programs/pdp_slp_l${l}_b8.slp.json" \
        || { echo "l=$l: sidecar differs from programs/pdp_slp_l${l}_b8.slp.json"; exit 1; }
}

corpus_of() { # L
    if [ "$1" = 13 ]; then echo "$HERE/corpus/corpus_l13_ps3_sample.txt"; else echo "$HERE/corpus/corpus_l$1.txt"; fi
}

cmd=${1:-}
[ $# -gt 0 ] && shift
case $cmd in
manifest)
    # Hardware and execution manifest (AGENTS.md "Hardware and placement for empirical benchmarks").
    js() { sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ' | sed 's/ *$//'; }
    lsc() { lscpu | sed -n "s/^$1: *//p" | head -1 | js; }
    cg() { v=$(cat "/sys/fs/cgroup/$1" 2>/dev/null | head -1 | js); echo "${v:-not exposed}"; }
    {
        printf '{\n'
        printf '  "date_utc": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        printf '  "cpu": {"vendor": "%s", "model_name": "%s", "family": "%s", "model": "%s", "stepping": "%s", "arch": "%s",\n' \
            "$(lsc 'Vendor ID')" "$(lsc 'Model name')" "$(lsc 'CPU family')" "$(lsc Model)" "$(lsc Stepping)" "$(uname -m)"
        printf '          "cpus": %s, "threads_per_core": "%s", "cores_per_socket": "%s", "sockets": "%s",\n' \
            "$(nproc)" "$(lsc 'Thread(s) per core')" "$(lsc 'Core(s) per socket')" "$(lsc 'Socket(s)')"
        printf '          "cache": {"L1d": "%s", "L1i": "%s", "L2": "%s", "L3": "%s"}},\n' \
            "$(lsc 'L1d cache')" "$(lsc 'L1i cache')" "$(lsc 'L2 cache')" "$(lsc 'L3 cache')"
        printf '  "os": {"kernel": "%s", "release": "%s", "virtualization": "%s", "hypervisor": "%s"},\n' \
            "$(uname -r)" "$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | tr -d '"' | js)" "$(lsc 'Virtualization type')" "$(lsc 'Hypervisor vendor')"
        printf '  "memory": {"total_kib": %s, "technology": "unknown", "note": "virtual machine: DIMM type, speed and channels are not exposed; not inferred from the CPU model"},\n' \
            "$(sed -n 's/^MemTotal: *\([0-9]*\) kB/\1/p' /proc/meminfo)"
        printf '  "limits": {"cgroup_cpu_max": "%s", "cgroup_memory_max": "%s", "cgroup_cpu_stat_nr_throttled": "%s"},\n' \
            "$(cg cpu.max)" "$(cg memory.max)" "$(cg cpu.stat | sed -n 's/^nr_throttled //p'; [ -r /sys/fs/cgroup/cpu.stat ] || echo 'not exposed')"
        printf '  "placement": {"cpus_allowed_list": "%s", "mems_allowed_list": "%s", "numa_nodes": %s, "cpu_affinity_policy": "none selected (the lock tool is not asked to pin; all exposed CPUs allowed)", "memory_policy": "default",\n' \
            "$(sed -n 's/^Cpus_allowed_list:[[:space:]]*//p' /proc/self/status)" "$(sed -n 's/^Mems_allowed_list:[[:space:]]*//p' /proc/self/status)" \
            "$(ls /sys/devices/system/node 2>/dev/null | grep -c '^node[0-9]' || true)"
        printf '                "note": "one NUMA node exposed: no NUMA locality comparison and no host-level isolation is claimed; affinity does not reserve a core from other processes"},\n'
        printf '  "co_runners_at_manifest_time": "%s",\n' "$(ps -eo comm,pcpu --sort=-pcpu | sed -n '2,6p' | tr '\n' ';' | js)"
        printf '  "isolation_tier": "none: exploratory. Run through the shared benchmark lock (busy), not an isolated-benchmark receipt; no timing ratio here is a claim",\n'
        printf '  "tools": {"cc": "%s", "nvcc": "%s", "nvdisasm": "%s"},\n' "$(${CC:-cc} --version | head -1 | js)" \
            "$( { ${NVCC:-nvcc} --version 2>/dev/null | sed -n 's/^Cuda compilation tools, //p' | js; } || true)" \
            "$( { ${NVDISASM:-nvdisasm} --version 2>/dev/null | sed -n 's/^Cuda compilation tools, //p' | head -1 | js; } || true)"
        printf '  "gpu": {"devices": [], "note": "no GPU in this environment; nvidia-smi %s; every number in this record is a CPU or compile-time number"},\n' \
            "$(command -v nvidia-smi >/dev/null 2>&1 && echo present || echo absent)"
        printf '  "revision": {"repo_head": "%s", "pdp_speedup_binary_sha256": "%s"},\n' "$(git -C "$REPO" rev-parse HEAD)" \
            "$(sha256sum "$PDP_SPEEDUP" 2>/dev/null | cut -d' ' -f1)"
        printf '  "source_sha256": {\n'
        for f in "$REPO"/suite/cuda/pdp_ps5_* "$REPO"/suite/cuda/build_pdp_ps5.sh "$HERE/run_ps5.sh"; do
            printf '    "%s": "%s",\n' "${f#"$REPO"/}" "$(sha256sum "$f" | cut -d' ' -f1)"
        done
        printf '    "_end": ""},\n'
        printf '  "built_binary_sha256": {\n'
        for f in "$OUT"/bin/pdp_ps5_emit "$OUT"/bin/pdp_ps5_parity_l* "$OUT"/bin/pdp_ps5_selftest_l*; do
            [ -f "$f" ] && printf '    "%s": "%s",\n' "$(basename "$f")" "$(sha256sum "$f" | cut -d' ' -f1)"
        done
        printf '    "_end": ""}\n'
        printf '}\n'
    } > "$RAW/manifest.json"
    cat "$RAW/manifest.json"
    ;;
build)
    MODE=${1:-plain}
    for l in ${PS5_RUNGS:-8 9 10 11 12}; do export_program "$l"; done
    LIST=
    for l in ${PS5_RUNGS:-8 9 10 11 12}; do LIST="$LIST $OUT/prog/pdp_slp_l${l}_b8.slp"; done
    # shellcheck disable=SC2086
    OUT=$OUT "$REPO/suite/cuda/build_pdp_ps5.sh" -o "$OUT" -m "$MODE" $LIST 2>&1 \
        | tee "$RAW/build_${MODE}_l$(echo "${PS5_RUNGS:-8 9 10 11 12}" | tr ' ' '-').log"
    mkdir -p "$RAW/emit"
    for l in ${PS5_RUNGS:-8 9 10 11 12}; do cp "$OUT/log/emit_l$l.json" "$RAW/emit/"; done
    ;;
selftest)
    L=$1
    REPS=${2:-100}
    MODE=${3:-plain}
    SUF=; [ "$MODE" = model ] && SUF=_model
    "$OUT/bin/pdp_ps5_selftest_l$L$SUF" --corpus "$(corpus_of "$L")" \
        --program "$OUT/prog/pdp_slp_l${L}_b8.slp" --reps "$REPS" | tee -a "$RAW/selftest_l$L$SUF.jsonl"
    ;;
parity)
    L=$1
    T=${2:-2}
    MODE=${3:-plain}
    SUF=; [ "$MODE" = model ] && SUF=_model
    EXTRA=
    if [ -n "$(digest_of "$L" verdicts)" ]; then
        EXTRA="--expect-verdicts $(digest_of "$L" verdicts) --expect-roots $(digest_of "$L" roots)"
    fi
    # shellcheck disable=SC2086
    "$OUT/bin/pdp_ps5_parity_l$L$SUF" --corpus "$(corpus_of "$L")" --threads "$T" $EXTRA \
        --expect-program-sha "$(prog_sha "$L")" | tee -a "$RAW/parity_l$L$SUF.jsonl"
    ;;
sanitize)
    # The emulation object (generated code) is not instrumented; the drivers and headers are.
    D=$REPO/suite/cuda
    SF="-std=c11 -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=undefined -Wall -Wextra"
    # shellcheck disable=SC2086
    cc $SF -DPS5_PARAMS_H="\"pdp_ps5_l8.h\"" -I"$OUT/gen" -I"$D" "$D/pdp_ps5_parity.c" "$OUT/bin/emulate_l8.o" -lpthread -o "$OUT/bin/asan_parity_l8"
    # shellcheck disable=SC2086
    cc $SF -DPS5_PARAMS_H="\"pdp_ps5_l8.h\"" -I"$OUT/gen" -I"$D" "$D/pdp_ps5_selftest.c" "$OUT/bin/emulate_l8.o" -lpthread -o "$OUT/bin/asan_selftest_l8"
    {
        echo "# ASan+UBSan (leak check on) on the host driver and self-test at l = 8; the emulation object is not instrumented"
        set +e
        "$OUT/bin/asan_parity_l8" --corpus "$HERE/corpus/corpus_l8.txt" --threads 3 --expect-program-sha "$(prog_sha 8)" > "$OUT/asan_p.out" 2>&1
        echo "parity exit=$?"; cut -c1-160 "$OUT/asan_p.out"
        "$OUT/bin/asan_selftest_l8" --corpus "$HERE/corpus/corpus_l8.txt" --program "$OUT/prog/pdp_slp_l8_b8.slp" --reps 5 > "$OUT/asan_s.out" 2>&1
        echo "selftest exit=$?"; cut -c1-160 "$OUT/asan_s.out"
        set -e
    } > "$RAW/sanitizers_l8.txt" 2>&1
    cat "$RAW/sanitizers_l8.txt"
    ;;
nvcc)
    L=$1
    : "${NVCC:?set NVCC to the nvcc binary}"
    export_program "$L"
    OUT=$OUT "$REPO/suite/cuda/build_pdp_ps5.sh" -o "$OUT" -m plain -n "$NVCC" "$OUT/prog/pdp_slp_l${L}_b8.slp" \
        2>&1 | tee "$RAW/nvcc_l$L.log"
    ;;
*)
    echo "usage: $0 manifest|build|selftest|parity|nvcc ..." >&2
    exit 2
    ;;
esac
