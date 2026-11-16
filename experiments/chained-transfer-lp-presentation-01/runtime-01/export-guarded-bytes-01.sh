#!/usr/bin/env bash
# Metadata/file custody only. This snapshot is not a runtime Git checkout,
# original checkpoint, source-built image, ABI qualification or paid admission.
set -euo pipefail
if [[ ${1:-} == --copy ]];then
 [[ $# == 4 ]] || exit 2
 repo=$2;producer=$3;out=$4
 while IFS=$'\t' read -r sha original member;do
  case $original in ../crypto/*) source=$producer/${original#../crypto/};;*) source=$repo/$original;;esac
  destination=$out/whole-guarded-files/$member
  mkdir -p -- "$(dirname -- "$destination")"
  cp --dereference --preserve=mode,timestamps -- "$source" "$destination"
  printf '%s  %s\n' "$sha" "$member" >> "$out/all-materialized-whole-files.sha256"
 done < "$out/entire-unique-source-plan.tsv"
 exit 0
fi
[[ $# == 3 ]] || exit 2
repo=$(realpath -e "$1")
producer=$(realpath -e "$2")
out=$(realpath -m "$3")
[[ $(realpath -e "$repo/../crypto") == "$producer" && ! -e $out ]]
[[ $out != "$repo" && $out != "$repo/"* && $out != "$producer" && $out != "$producer/"* ]]
mkdir "$out"
cd "$repo"
cp "$0" "$out/entire-actual-export-command.sh"
date -u +%FT%TZ > "$out/start.txt"
git rev-parse HEAD > "$out/actual-Consumer-checkout-HEAD.txt"
git -C "$producer" rev-parse HEAD > "$out/actual-Root-checkout-HEAD.txt"
finish(){ local code=$?;trap - EXIT;printf '%s\n' "$code" > "$out/original.exit";date -u +%FT%TZ > "$out/finish.txt";exit "$code"; }
trap finish EXIT
phase(){
 local name=$1 code;shift
 jq --null-input --args '$ARGS.positional' -- "$@" > "$out/$name.argv.json"
 set +e
 (ulimit -v 2097152;exec timeout --signal=TERM --kill-after=5s 120 "$@") > "$out/$name.stdout" 2> "$out/$name.stderr"
 code=$?;set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s\n' "$name" "$code" >> "$out/all-actual-byte-phases.txt"
 return "$code"
}
guards=(experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256
 experiments/chained-transfer-lp-presentation-01/historical-01/source-01.sha256
 experiments/chained-transfer-lp-presentation-01/population-01/source-01.sha256)
declare -A hashes=()
index=0
for guard in "${guards[@]}";do
 phase "initial-guard-$index" sha256sum --check "$guard"
 cp "$guard" "$out/entire-original-guard-$index.sha256"
 while IFS= read -r line;do
  sha=${line:0:64};name=${line:66}
  [[ $sha =~ ^[0-9a-f]{64}$ && ${line:64:2} == '  ' ]]
  if [[ -v hashes[$name] ]];then [[ ${hashes[$name]} == "$sha" ]];else hashes[$name]=$sha;fi
 done < "$guard"
 # Include the guard files themselves; a manifest cannot contain its own hash.
 sha=$(sha256sum "$guard");sha=${sha:0:64}
 if [[ -v hashes[$guard] ]];then [[ ${hashes[$guard]} == "$sha" ]];else hashes[$guard]=$sha;fi
 index=$((index+1))
done
for name in "${!hashes[@]}";do
 [[ $name != /* && $name != *$'\t'* && $name != *$'\r'* && $name != *$'\n'* && $name != *'\'* ]]
 case $name in ../crypto/*) relative=${name#../crypto/};member=crypto/$relative;;*) relative=$name;member=cryptanalysis/$relative;;esac
 [[ $relative != '..' && $relative != ../* && $relative != */../* && $relative != */.. ]]
 printf '%s\t%s\t%s\n' "${hashes[$name]}" "$name" "$member" >> "$out/entire-unsorted-source-plan.tsv"
done
LC_ALL=C sort -- "$out/entire-unsorted-source-plan.tsv" > "$out/entire-unique-source-plan.tsv"
phase materialize-every-whole-guarded-file bash "$0" --copy "$repo" "$producer" "$out"
phase all-materialized-file-bytes bash -c 'cd "$1" && exec sha256sum --check "$2"' _ "$out/whole-guarded-files" "$out/all-materialized-whole-files.sha256"
phase archive-every-whole-guarded-file tar --create --format=posix --file "$out/entire-guarded-file-snapshot.tar" --directory "$out/whole-guarded-files" crypto cryptanalysis
phase compare-entire-archive-against-every-materialized-file tar --compare --file "$out/entire-guarded-file-snapshot.tar" --directory "$out/whole-guarded-files"
for index in "${!guards[@]}";do
 phase "final-original-guard-$index" sha256sum --check "${guards[$index]}"
 phase "original-guard-$index-byte-equality" cmp "${guards[$index]}" "$out/entire-original-guard-$index.sha256"
done
phase final-all-materialized-file-bytes bash -c 'cd "$1" && exec sha256sum --check "$2"' _ "$out/whole-guarded-files" "$out/all-materialized-whole-files.sha256"
sha256sum "$out/entire-guarded-file-snapshot.tar" > "$out/entire-archive.sha256"
wc -l < "$out/entire-unique-source-plan.tsv" > "$out/actual-whole-member-count.txt"
printf '%s\n' 'Whole named source/input files and guard bytes only; no .git, current RESUME, runtime binary, decoded fixture preparation or credential is supplied by this snapshot. Actual checkout heads and actual command bytes are recorded separately; no claim that an unpublished exporter belongs to those heads. Runtime/source publication/checkpoint/OCI/ABI/admission remain separate.' > "$out/scope.txt"
