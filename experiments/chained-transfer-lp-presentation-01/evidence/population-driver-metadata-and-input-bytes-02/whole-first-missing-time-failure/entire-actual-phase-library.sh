#!/usr/bin/env bash
# Process accounting only; no launch or scientific algorithm.
phase() {
 local name=$1 limit=$2 expected_exit=$3 left code;shift 3
 [[ $name =~ ^[a-z0-9-]+$ && ! -e $out/$name.exit ]]
 left=$(remaining) || return 125
 (( left >= limit )) || limit=$left
 jq --null-input --args '$ARGS.positional' -- "$@" > "$out/$name.argv.json"
 date -u +%FT%TZ > "$out/$name.start"
 set +e
 (
  ulimit -v 2097152
  exec timeout --signal=TERM --kill-after=5s "$limit" /usr/bin/time -v -o "$out/$name.time" "$@"
 ) > "$out/$name.stdout" 2> "$out/$name.stderr" &
 current_pid=$!
 wait "$current_pid"
 code=$?;current_pid=''
 set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 date -u +%FT%TZ > "$out/$name.finish"
 printf '%s actual=%s expected=%s\n' "$name" "$code" "$expected_exit" >> "$out/all-actual-phases.txt"
 (( code == expected_exit )) || { (( code != 0 )) && return "$code";return 2; }
 sync_results "$name"
}
helper() { phase "$1" 120 0 "${@:2}"; }
native() { phase "$1" 900 0 "${@:2}"; }
reject() { phase "$1" 900 1 "${@:2}"; }

