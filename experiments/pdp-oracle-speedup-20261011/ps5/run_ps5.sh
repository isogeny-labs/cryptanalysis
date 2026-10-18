#!/bin/sh
# run_ps5.sh - PS-5 on a CPU-only host: build the kernel's emulation from
# PS-3's recorded program and replay the PS-0 corpus through it.
#
#   run_ps5.sh manifest            hardware/toolchain manifest -> raw/manifest.json
#   run_ps5.sh build  [MODE]       unpack + hash-check programs, emit, build (MODE plain|model; default plain)
#   run_ps5.sh selftest L [REPS]   truth tables, every wire, the function (raw/selftest_lL.jsonl)
#   run_ps5.sh parity   L [THREADS] [MODE]   corpus replay (raw/parity_lL[_model].jsonl)
#   run_ps5.sh nvcc   L            compile the CUDA kernel (needs $NVCC; no device is used)
#
# Heavy steps are meant to be run as
#   python3 <crypto>/tools/isolated_bench.py busy --wait -- experiments/pdp-oracle-speedup-20261011/ps5/run_ps5.sh ...
# $OUT (default: a directory next to this script's scratch use) holds the build.
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
    esac
}
# PS-0's digests for run 1 of rung L (baseline_v1/digests.txt, copied as expected_digests_ps0.txt).
digest_of() { # L which(verdicts|roots)
    awk -v l="l=$1" -v w="digest_$2" '$1=="run=1" && $2==l { for (i=1;i<=NF;i++) if ($i==w) print $(i+1) }' \
        "$HERE/expected_digests_ps0.txt"
}

cmd=${1:-}
[ $# -gt 0 ] && shift
case $cmd in
manifest)
    {
        printf '{\n'
        printf '  "date_utc": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        printf '  "host": {"cpu_model": "%s", "cpus": %s, "kernel": "%s", "arch": "%s"},\n' \
            "$(grep -m1 'model name' /proc/cpuinfo | sed 's/.*: //')" "$(nproc)" "$(uname -r)" "$(uname -m)"
        printf '  "virtualization": "%s",\n' "$(lscpu | sed -n 's/^Hypervisor vendor: *//p')"
        printf '  "memory_kib": %s,\n' "$(sed -n 's/^MemTotal: *\([0-9]*\) kB/\1/p' /proc/meminfo)"
        printf '  "cc": "%s",\n' "$(${CC:-cc} --version | head -1)"
        printf '  "nvcc": "%s",\n' "$( { ${NVCC:-nvcc} --version 2>/dev/null | tail -2 | head -1; } || true)"
        printf '  "gpu": {"devices": [], "note": "no GPU in this environment; nvidia-smi %s"},\n' \
            "$(command -v nvidia-smi >/dev/null 2>&1 && echo present || echo absent)"
        printf '  "repo_head": "%s",\n' "$(git -C "$REPO" rev-parse HEAD)"
        printf '  "numa_nodes": "%s"\n' "$(ls /sys/devices/system/node 2>/dev/null | grep -c '^node[0-9]' || true)"
        printf '}\n'
    } > "$RAW/manifest.json"
    cat "$RAW/manifest.json"
    ;;
build)
    MODE=${1:-plain}
    mkdir -p "$OUT/prog"
    for l in 8 9 10 11 12; do
        zcat "$HERE/programs/pdp_slp_l${l}_b8.slp.gz" > "$OUT/prog/pdp_slp_l${l}_b8.slp"
        cp "$HERE/programs/pdp_slp_l${l}_b8.slp.json" "$OUT/prog/"
        got=$(sha256sum "$OUT/prog/pdp_slp_l${l}_b8.slp" | cut -d' ' -f1)
        [ "$got" = "$(prog_sha $l)" ] || { echo "l=$l: program hash $got differs from PS-2's"; exit 1; }
    done
    LIST=
    for l in ${PS5_RUNGS:-8 9 10 11 12}; do LIST="$LIST $OUT/prog/pdp_slp_l${l}_b8.slp"; done
    # shellcheck disable=SC2086
    OUT=$OUT "$REPO/suite/cuda/build_pdp_ps5.sh" -o "$OUT" -m "$MODE" $LIST 2>&1 | tee "$RAW/build_$MODE.log"
    ;;
selftest)
    L=$1
    REPS=${2:-100}
    "$OUT/bin/pdp_ps5_selftest_l$L" --corpus "$HERE/corpus/corpus_l$L.txt" \
        --program "$OUT/prog/pdp_slp_l${L}_b8.slp" --reps "$REPS" | tee -a "$RAW/selftest_l$L.jsonl"
    ;;
parity)
    L=$1
    T=${2:-2}
    MODE=${3:-plain}
    SUF=; [ "$MODE" = model ] && SUF=_model
    "$OUT/bin/pdp_ps5_parity_l$L$SUF" --corpus "$HERE/corpus/corpus_l$L.txt" --threads "$T" \
        --expect-verdicts "$(digest_of "$L" verdicts)" --expect-roots "$(digest_of "$L" roots)" \
        --expect-program-sha "$(prog_sha "$L")" | tee -a "$RAW/parity_l$L$SUF.jsonl"
    ;;
nvcc)
    L=$1
    : "${NVCC:?set NVCC to the nvcc binary}"
    mkdir -p "$OUT/prog"
    zcat "$HERE/programs/pdp_slp_l${L}_b8.slp.gz" > "$OUT/prog/pdp_slp_l${L}_b8.slp"
    cp "$HERE/programs/pdp_slp_l${L}_b8.slp.json" "$OUT/prog/"
    OUT=$OUT "$REPO/suite/cuda/build_pdp_ps5.sh" -o "$OUT" -m plain -n "$NVCC" "$OUT/prog/pdp_slp_l${L}_b8.slp" \
        2>&1 | tee "$RAW/nvcc_l$L.log"
    ;;
*)
    echo "usage: $0 manifest|build|selftest|parity|nvcc ..." >&2
    exit 2
    ;;
esac
