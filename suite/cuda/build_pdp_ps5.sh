#!/bin/sh
# build_pdp_ps5.sh - generate and build the PS-5 kernel for one or more
# `pdp-slp/1` programs.
#
#   suite/cuda/build_pdp_ps5.sh [-o OUT] [-m plain|model] [-n NVCC] PROGRAM.slp...
#
# For each PROGRAM.slp (with its PROGRAM.slp.json sidecar):
#   1. pdp_ps5_emit writes OUT/pdp_ps5_l<L>.h and .inc (the straight-line code),
#      refusing a program whose SHA-256 differs from its sidecar's;
#   2. the host emulation is built from the same two files:
#        OUT/bin/pdp_ps5_parity_l<L>    corpus replay (pdp_ps5_parity.c)
#        OUT/bin/pdp_ps5_selftest_l<L>  truth tables, every wire, the function
#      -m plain  (default) runs the gates as C operators, which compiles in
#                about half the time; the self-test proves the five lop3
#                tables equal those operators
#      -m model  runs every gate through the bitwise model of lop3 with its
#                table (the form in which the device executes it)
#   3. with -n NVCC (or $NVCC), the CUDA kernel is compiled to PTX (nvcc -ptx)
#      and assembled by ptxas for $PS5_ARCHS (default sm_80) with its register
#      and spill report; with $NVDISASM the cubin's SASS is counted.  This is
#      a compile check; nothing is ever run on a device here.
#
# Host compilers do not finish the 65,000-100,000 local variables of the
# device form in minutes, so the host build keeps the wires in an array and the
# emitter's chunk markers split the body into functions
# (PS5_WIRES_IN_MEMORY; see pdp_ps5_device.cuh).  gcc is slow on the stores
# of that array, hence -fno-tree-dse -fno-dse.
set -eu

DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
OUT=${OUT:-$(mktemp -d)}
MODE=plain
NVCC=${NVCC:-}
CC=${CC:-cc}
while getopts "o:m:n:" opt; do
    case $opt in
        o) OUT=$OPTARG ;;
        m) MODE=$OPTARG ;;
        n) NVCC=$OPTARG ;;
        *) echo "usage: $0 [-o OUT] [-m plain|model] [-n NVCC] PROGRAM.slp..." >&2; exit 2 ;;
    esac
done
shift $((OPTIND - 1))
[ $# -ge 1 ] || { echo "no program given" >&2; exit 2; }
mkdir -p "$OUT/bin" "$OUT/gen" "$OUT/log"

CFLAGS_HOST="-std=c11 -O1 -Wall -Wextra -pedantic"
if "$CC" --version 2>/dev/null | grep -qi gcc; then CFLAGS_HOST="$CFLAGS_HOST -fno-tree-dse -fno-dse"; fi
[ "$MODE" = plain ] && MODEFLAG=-DPS5_PLAIN_OPS || MODEFLAG=
SUFFIX=
[ "$MODE" = model ] && SUFFIX=_model

"$CC" -std=c11 -O2 -Wall -Wextra -pedantic -o "$OUT/bin/pdp_ps5_emit" "$DIR/pdp_ps5_emit.c"

status=0
for prog in "$@"; do
    l=$(sed -n 's/.*"l":\([0-9]*\).*/\1/p' "$prog.json")
    summary=$("$OUT/bin/pdp_ps5_emit" "$prog" "$OUT/gen/pdp_ps5_l$l")
    printf '%s\n' "$summary" > "$OUT/log/emit_l$l.json"
    echo "l=$l: $summary"
    P="-DPS5_PARAMS_H=\"pdp_ps5_l$l.h\" -I$OUT/gen -I$DIR"
    # shellcheck disable=SC2086
    "$CC" $CFLAGS_HOST $MODEFLAG -DPS5_WIRES_IN_MEMORY $P -c "$DIR/pdp_ps5_emulate.c" \
        -o "$OUT/bin/emulate_l$l$SUFFIX.o"
    # shellcheck disable=SC2086
    "$CC" $CFLAGS_HOST $P "$DIR/pdp_ps5_parity.c" "$OUT/bin/emulate_l$l$SUFFIX.o" -lpthread \
        -o "$OUT/bin/pdp_ps5_parity_l$l$SUFFIX"
    # shellcheck disable=SC2086
    "$CC" $CFLAGS_HOST $P "$DIR/pdp_ps5_selftest.c" "$OUT/bin/emulate_l$l$SUFFIX.o" -lpthread \
        -o "$OUT/bin/pdp_ps5_selftest_l$l$SUFFIX"
    echo "l=$l: host emulation built ($MODE)"

    if [ -n "$NVCC" ]; then
        # nvcc's own pipeline is cicc (to PTX) then ptxas (to SASS); run apart so that each is timed.
        ptx="$OUT/pdp_ps5_l$l.ptx"
        t0=$(date +%s)
        "$NVCC" -arch=compute_80 -O3 -ptx -I"$OUT/gen" -I"$DIR" -DPS5_PARAMS_H="\"pdp_ps5_l$l.h\"" \
            -o "$ptx" "$DIR/pdp_ps5_kernel.cu"
        echo "l=$l ptx: $ptx ($(grep -c 'lop3.b32' "$ptx") lop3.b32 instructions; nvcc -ptx took $(( $(date +%s) - t0 )) s)"
        PTXAS=$(dirname "$NVCC")/ptxas
        [ -x "$PTXAS" ] || PTXAS=ptxas
        for arch in ${PS5_ARCHS:-sm_80}; do
            cubin="$OUT/pdp_ps5_l${l}_$arch.cubin"
            t0=$(date +%s)
            log=$("$PTXAS" -arch="$arch" -O3 -v -o "$cubin" "$ptx" 2>&1) || {
                echo "$log" | tail -20
                echo "l=$l $arch: ptxas failed"
                status=1
                continue
            }
            echo "$log" > "$OUT/log/ptxas_l${l}_$arch.txt"
            echo "l=$l $arch: $(echo "$log" | grep -E 'registers|spill' | sed 's/ptxas info *: //' | tr '\n' ' ') (ptxas took $(( $(date +%s) - t0 )) s)"
            [ -s "$cubin" ] || { echo "l=$l $arch: no cubin"; status=1; }
            if [ -n "${NVDISASM:-}" ]; then
                "$NVDISASM" -c "$cubin" | grep -E '^[[:space:]]+/\*[0-9a-f]{4,}\*/[[:space:]]+(@!?U?P[0-9T][[:space:]]+)?[A-Z]' \
                    | sed -E 's/^[[:space:]]+\/\*[0-9a-f]+\*\/[[:space:]]+(@!?U?P[0-9T][[:space:]]+)?//' > "$OUT/log/sass_l${l}_$arch.txt"
                { echo "sass instructions: $(wc -l < "$OUT/log/sass_l${l}_$arch.txt")"
                  awk '{ op=$1; sub(/[;,].*/,"",op); split(op,b,"."); c[b[1]]++ } END { for (k in c) print c[k], k }' \
                      "$OUT/log/sass_l${l}_$arch.txt" | sort -rn
                  echo "LOP3 tables:"
                  grep '^LOP3' "$OUT/log/sass_l${l}_$arch.txt" | sed -E 's/.*, (0x[0-9a-f]+), !?[A-Z]+ ;.*/\1/' | sort | uniq -c | sort -rn
                } > "$OUT/log/sass_hist_l${l}_$arch.txt"
                echo "l=$l $arch: SASS histogram in $OUT/log/sass_hist_l${l}_$arch.txt"
            fi
        done
    fi
done
exit $status
