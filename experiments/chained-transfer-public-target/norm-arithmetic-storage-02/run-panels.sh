#!/usr/bin/env bash
# Thin sequential native orchestration. Every result/count comparison is Rust.
set -euo pipefail
[[ $# == 3 ]] || exit 2
exe=$(realpath "$1")
fixture=$(realpath "$2")
out=$(realpath -m "$3")
[[ ! -e $out && -f $exe && -f $fixture ]] || exit 2
mkdir "$out"
cp "$exe" "$out/census.bin"
cp "$fixture" "$out/cases60.json"
sha256sum "$out/census.bin" "$out/cases60.json" > "$out/frozen-inputs.sha256"
cp "$0" "$out/original-command.sh"
cat > "$out/cold.sh" <<'COLD'
#!/usr/bin/env bash
set -u
cd -- "$(dirname -- "$0")"
export N4_ARITHMETIC_OBSERVER=enabled
ulimit -v 2097152
for i in {0..59}; do
 for arm in baseline direct; do
  date -u +%FT%TZ > "cold-$arm-$i.start"
  ./census.bin --case cases60.json "$arm" "$i" > "cold-$arm-$i.txt" 2>&1
  status=$?
  printf '%s\n' "$status" > "cold-$arm-$i.exit"
  date -u +%FT%TZ > "cold-$arm-$i.finish"
  [[ $status == 0 ]] || exit "$status"
 done
done
COLD
cat > "$out/reused.sh" <<'REUSED'
#!/usr/bin/env bash
set -u
cd -- "$(dirname -- "$0")"
export N4_ARITHMETIC_OBSERVER=enabled
ulimit -v 2097152
for arm in baseline direct; do
 date -u +%FT%TZ > "reused-$arm.start"
 ./census.bin --reused cases60.json "$arm" > "reused-$arm.txt" 2>&1
 status=$?
 printf '%s\n' "$status" > "reused-$arm.exit"
 date -u +%FT%TZ > "reused-$arm.finish"
 [[ $status == 0 ]] || exit "$status"
done
REUSED
set +e
timeout 900 bash "$out/cold.sh" > "$out/cold-caller.txt" 2>&1
cold=$?
set -e
printf '%s\n' "$cold" > "$out/cold-panel.exit"
# A timeout leaves a distinct reuse question unblocked; a semantic failure does not.
if [[ $cold != 0 && $cold != 124 ]]; then exit "$cold"; fi
set +e
timeout 900 bash "$out/reused.sh" > "$out/reused-caller.txt" 2>&1
reused=$?
set -e
printf '%s\n' "$reused" > "$out/reused-panel.exit"
sha256sum --check "$out/frozen-inputs.sha256" > "$out/final-input-guards.txt"
if [[ $cold != 0 ]]; then exit "$cold"; fi
exit "$reused"
