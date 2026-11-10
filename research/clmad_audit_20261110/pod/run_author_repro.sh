#!/usr/bin/env bash
# Addendum run (protocol amendment A1, 2026-11-10, recorded before this ran):
# execute the third-party reproducer unchanged, as published at
# github.com/robik75/ptxas-clmad-constant-operand, next to ours, so that
# "not reproduced with an independent reproducer" can be told apart from
# "the reported defect is not present on this toolkit and GPU".  The
# repository has no licence, so its source is not copied into ours: it is
# cloned on the pod, its commit hash recorded, and only its output kept.
set -u
cd /work/bundle || exit 9
OUT=/work/results
mkdir -p "$OUT"
{
  echo "## date"; date -u
  nvidia-smi --query-gpu=name,uuid,driver_version,compute_cap,clocks.max.sm --format=csv || true
  echo "## nvcc"; nvcc --version | tail -2
  echo "## ptxas"; ptxas --version | tail -1
} > "$OUT/env.txt" 2>&1
apt-get install -y -qq git >/dev/null 2>&1
rm -rf /work/author && git clone -q https://github.com/robik75/ptxas-clmad-constant-operand /work/author
cd /work/author || { echo "clone failed" > "$OUT/author_clone_failed"; exit 0; }
git rev-parse HEAD > "$OUT/author_commit.txt"
sha256sum repro.cu run.sh > "$OUT/author_sha256.txt"
chmod +x run.sh
# Their script, their flags.
./run.sh > "$OUT/author_run_default.txt" 2>&1
echo "exit=$?" >> "$OUT/author_run_default.txt"
./run.sh -DN=16 > "$OUT/author_run_N16.txt" 2>&1
echo "exit=$?" >> "$OUT/author_run_N16.txt"
for n in 15 18 19; do
  ./run.sh -DN=$n > "$OUT/author_run_N$n.txt" 2>&1
  echo "exit=$?" >> "$OUT/author_run_N$n.txt"
done
ls -la out > "$OUT/author_out_listing.txt" 2>&1
for b in out/*; do [ -x "$b" ] && [ -f "$b" ] && echo "$b $(cuobjdump -sass "$b" 2>/dev/null | grep -c CLMAD)" >> "$OUT/author_clmad_sass_counts.txt"; done
cp run.sh "$OUT/author_run.sh.txt" 2>/dev/null
cd /work && tar -cJf /work/results.tar.xz results && sha256sum results.tar.xz > results.sha256
echo done
