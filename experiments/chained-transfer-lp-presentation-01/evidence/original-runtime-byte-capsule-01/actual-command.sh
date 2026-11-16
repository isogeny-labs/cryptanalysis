#!/usr/bin/env bash
# Whole original artifact/native/prepared byte custody only. Never execute the
# original binaries or call this an original-engine cold compilation.
set -euo pipefail
[[ $# == 2 ]] || exit 2
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
archive=$(realpath -e "$1")
out=$(realpath -m "$2")
[[ ! -e $out && -f $archive && ! -L $archive ]] || exit 2
[[ $archive != *$'\n'* && $out != *$'\n'* ]] || exit 2
mkdir "$out"
cp "$0" "$out/actual-command.sh"
cp "$pkg/manifest-01.json" "$out/entire-original-runtime-manifest.json"
cp "$pkg/selected-members-01.sha256" "$out/entire-selected-member-pins.sha256"
phase() {
 local name=$1 code;shift
 set +e
 "$@" > "$out/$name.stdout" 2> "$out/$name.stderr"
 code=$?
 set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s\n' "$name" "$code" >> "$out/all-actual-metadata-phases.txt"
 return "$code"
}
finish() {
 local code=$?;trap - EXIT
 printf '%s\n' "$code" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 exit "$code"
}
trap finish EXIT
date -u +%FT%TZ > "$out/start.txt"
bounded() (ulimit -v 2097152; exec timeout 120 "$@")
sha=$(jq --raw-output '.original_archive.sha256' "$pkg/manifest-01.json")
bytes=$(jq --raw-output '.original_archive.bytes' "$pkg/manifest-01.json")
[[ $sha =~ ^[0-9a-f]{64}$ && $(wc -c < "$archive") == "$bytes" ]]
printf '%s  %s\n' "$sha" "$archive" > "$out/entire-archive-reference.sha256"
phase whole-original-archive-bytes bounded sha256sum --check "$out/entire-archive-reference.sha256"
mapfile -t members < <(jq --raw-output '.members_used_without_execution[].archive_path' "$pkg/manifest-01.json")
[[ ${#members[@]} -gt 20 && ${#members[@]} -lt 2000 ]]
for name in "${members[@]}";do
 [[ $name == n4-original-relation-output/* && $name != *'..'* && $name != *$'\n'* ]] || exit 2
done
phase materialize-complete-selected-members bounded unzip -qq "$archive" "${members[@]}" -d "$out/entire-original-members-used"
phase exact-every-selected-member bounded bash -c 'cd "$1" && exec sha256sum --check "$2"' _ "$out/entire-original-members-used" "$pkg/selected-members-01.sha256"
base=$out/entire-original-members-used/n4-original-relation-output
for label in rank-replay character-auditor;do
 phase "$label-original-compile-runtime-byte-equality" bounded cmp "$base/actual-compiled-$label.bin" "$base/actual-runtime-$label.bin"
 phase "$label-original-profile-and-custody" jq --exit-status '.mode=="runtime" and .whole_compiled_runtime_equal==true and .actual_Cargo_artifact.profile.opt_level=="3" and .actual_Cargo_artifact.profile.test==false' "$base/$label-runtime-custody.json"
done
phase original-complete-engine-reuse jq --exit-status '.actual_reuse==true and .actual_prepared_bytes_unchanged==true and (.actual_aliases|length)==2' "$base/engine-reused-character-auditor.json"
mkdir "$out/native"
cp "$base/actual-runtime-rank-replay.bin" "$out/native/original-rank-replayer"
cp "$base/actual-runtime-character-auditor.bin" "$out/native/original-character-auditor"
chmod +x "$out/native/original-rank-replayer" "$out/native/original-character-auditor"
phase final-rank-native-equality bounded cmp "$base/actual-runtime-rank-replay.bin" "$out/native/original-rank-replayer"
phase final-character-native-equality bounded cmp "$base/actual-runtime-character-auditor.bin" "$out/native/original-character-auditor"
if ! ln "$archive" "$out/entire-original-artifact.zip" 2> "$out/whole-archive-hardlink.stderr";then
 phase copy-entire-original-archive bounded cp "$archive" "$out/entire-original-artifact.zip"
fi
printf '%s  %s\n' "$sha" "$out/entire-original-artifact.zip" > "$out/entire-capsule-archive-reference.sha256"
phase final-whole-capsule-archive bounded sha256sum --check "$out/entire-capsule-archive-reference.sha256"
phase final-every-selected-member bounded bash -c 'cd "$1" && exec sha256sum --check "$2"' _ "$out/entire-original-members-used" "$pkg/selected-members-01.sha256"
source=$(jq --raw-output '.original_archive.source_revision' "$pkg/manifest-01.json")
upstream=$(jq --raw-output '.original_archive.upstream_source_revision' "$pkg/manifest-01.json")
jq --null-input --arg source "$source" --arg upstream "$upstream" --arg sha "$sha" \
 '{schema:"whole-original-runtime-byte-custody/v1",original_source:$source,original_upstream_source:$upstream,entire_original_artifact_sha256:$sha,
   scope:"complete earlier artifact plus whole unchanged native/prepared/source byte custody only; no new original compilation or workload execution",
   original_engine_cold_120s_qualification:false,old_native_executed_during_assembly:false}' > "$out/complete-byte-custody.json"
