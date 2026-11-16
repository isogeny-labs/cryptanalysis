#!/usr/bin/env bash
# Offline process-accounting controls only. No population, native math, AWS,
# Kubernetes, compiler or original binary is invoked by these fixtures.
set -euo pipefail
[[ $# == 1 && ! -e $1 ]] || exit 2
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
out=$(realpath -m "$1")
mkdir "$out"
cp "$0" "$out/entire-actual-metadata-harness.sh"
cp "$pkg/phases-01.sh" "$out/entire-actual-phase-library.sh"
fixture() {
 local name=$1 wanted=$2 observed=$3 process=$4 code;shift 4
 mkdir "$out/$name"
 set +e
 bash -euo pipefail -c '
  out=$1;library=$2;expected=$3;process=$4;mode=$5
  current_pid=""
  remaining() { [[ $mode != deadline ]] || return 125;printf "1000\n"; }
  sync_results() { printf "%s\n" "$1" >> "$out/actual-upload-metadata-fixture.txt";[[ $mode != upload-fails ]] || return 91; }
  source "$library"
  case $process in
   timeout) phase control 1 "$expected" bash -c "sleep 3" ;;
   signal) phase control 1 "$expected" bash -c '\''kill -TERM $$'\'' ;;
   *) phase control 1 "$expected" bash -c "exit $process" ;;
  esac
  printf "reached\n" > "$out/after-phase.txt"
 ' _ "$out/$name" "$pkg/phases-01.sh" "$wanted" "$process" "${1:-normal}" \
  > "$out/$name/whole-caller.stdout" 2> "$out/$name/whole-caller.stderr"
 code=$?
 set -e
 printf '%s\n' "$code" > "$out/$name/whole-caller.exit"
 printf '%s actual=%s expected=%s\n' "$name" "$code" "$observed" >> "$out/all-actual-controls.txt"
 [[ $code == "$observed" ]]
 if [[ $observed == 0 ]];then [[ -f $out/$name/after-phase.txt ]];else [[ ! -e $out/$name/after-phase.txt ]];fi
}
fixture successful-positive 0 0 0
fixture actual-exit-one-rejection 1 0 1
fixture false-zero-rejection-is-error 1 2 0
fixture exit-two-is-not-rejection 1 2 2
fixture timeout-is-not-rejection 1 124 timeout
fixture signal-is-not-rejection 1 143 signal
fixture partial-upload-fails-closed 0 91 0 upload-fails
fixture deadline-prevents-process 0 125 0 deadline
[[ ! -e $out/deadline-prevents-process/control.argv.json ]]
printf '%s\n' 'Offline shell process/exit/deadline/upload metadata controls only; no mathematical computation, paid admission or full driver execution.' > "$out/scope.txt"
