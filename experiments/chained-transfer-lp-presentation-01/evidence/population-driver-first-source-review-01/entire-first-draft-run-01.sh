#!/usr/bin/env bash
# Prospective whole population, EKS only. This does not submit a build or Job.
# Admission, exact published image and externally observed Job/Pod/OCI identity
# must be established by the maintained launcher before this command is run.
set -euo pipefail
[[ $# == 6 ]] || exit 2
repo=$(realpath -e "$1")
expected=$2
inputs=$(realpath -e "$3")
bins=$(realpath -e "$4")
capsule=$(realpath -e "$5")
out=$(realpath -m "$6")
component=experiments/chained-transfer-lp-presentation-01
pkg=$repo/$component

# These are actual names from the unchanged submit-job, not a new API schema.
: "${POD_UID:?EKS downward-API Pod UID required}"
: "${NODE_NAME:?EKS downward-API node name required}"
: "${ISOLAB_JOB_ID:?isolab Job name required}"
: "${ISOLAB_RESULTS_URI:?unique Job/Pod results prefix required}"
: "${KUBERNETES_SERVICE_HOST:?EKS runtime required}"
: "${LP_ATTEMPT_STARTED_EPOCH:?freeze before launch}"
: "${LP_ABSOLUTE_DEADLINE_EPOCH:?freeze before launch}"
[[ $expected =~ ^[0-9a-f]{40}$ && $POD_UID =~ ^[0-9a-f-]{36}$ ]]
[[ $ISOLAB_JOB_ID =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ ]]
[[ $ISOLAB_RESULTS_URI == "s3://isolab-results-104186811093-us-east-2/runs/$ISOLAB_JOB_ID/$POD_UID/" ]]
[[ $LP_ATTEMPT_STARTED_EPOCH =~ ^[1-9][0-9]{9}$ && $LP_ABSOLUTE_DEADLINE_EPOCH =~ ^[1-9][0-9]{9}$ ]]
(( LP_ABSOLUTE_DEADLINE_EPOCH > LP_ATTEMPT_STARTED_EPOCH ))
(( LP_ABSOLUTE_DEADLINE_EPOCH <= LP_ATTEMPT_STARTED_EPOCH + 3600 ))
[[ $(git -C "$repo" rev-parse --show-toplevel) == "$repo" ]]
[[ $(git -C "$repo" rev-parse HEAD) == "$expected" ]]
[[ ! -e $out && $out != "$repo" && $out != "$repo/"* ]]
[[ $inputs != "$out" && $bins != "$out" && $capsule != "$out" ]]
[[ -z $(git -C "$repo" status --porcelain --untracked-files=all) ]]
cmp "$0" "$pkg/population-01/run-01.sh"
for exe in extract_public historical_certificates lp-post-character;do
 [[ -f $bins/$exe && ! -L $bins/$exe && -x $bins/$exe ]]
done
for exe in original-rank-replayer original-character-auditor;do
 [[ -f $capsule/native/$exe && ! -L $capsule/native/$exe && -x $capsule/native/$exe ]]
done
mkdir "$out"
cd "$repo"
complete=false
current_pid=''
date -u +%FT%TZ > "$out/start.txt"
printf '%s\n' "$expected" > "$out/actual-source-head.txt"
jq --null-input --arg job "$ISOLAB_JOB_ID" --arg pod "$POD_UID" --arg node "$NODE_NAME" \
 --arg results "$ISOLAB_RESULTS_URI" --argjson start "$LP_ATTEMPT_STARTED_EPOCH" \
 --argjson deadline "$LP_ABSOLUTE_DEADLINE_EPOCH" \
 '{job_name:$job,pod_uid_from_downward_api:$pod,node_name_from_downward_api:$node,
   results:$results,attempt_started_epoch:$start,absolute_deadline_epoch:$deadline,
   externally_observed_job_uid_and_OCI_digest_still_required:true,
   scope:"runtime environment metadata, not signed execution or paid admission"}' > "$out/runtime-context.json"

# Leave 60s of the frozen absolute deadline for final partial-result custody.
remaining() {
 local now;now=$(date -u +%s)
 (( now >= LP_ATTEMPT_STARTED_EPOCH && now < LP_ABSOLUTE_DEADLINE_EPOCH - 60 )) || return 125
 printf '%s\n' "$((LP_ABSOLUTE_DEADLINE_EPOCH - now - 60))"
}
sync_results() {
 local left cap
 left=$(remaining) || return 125
 cap=120;(( left >= cap )) || cap=$left
 timeout --signal=TERM --kill-after=5s "$cap" aws --region us-east-2 s3 sync \
   "$out/" "$ISOLAB_RESULTS_URI" --only-show-errors
}
finish() {
 local original=$? upload=0 now left cap
 trap - EXIT TERM INT
 set +e
 if [[ -n $current_pid ]];then
  kill -TERM "$current_pid" 2>/dev/null
  wait "$current_pid"
 fi
 printf '%s\n' "$original" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 jq --null-input --argjson code "$original" --argjson complete "$complete" \
   '{original_exit:$code,all_frozen_phases_complete:$complete,
     scope:"unsigned whole-population process data; external artifact/UID reconciliation required"}' > "$out/process-outcome.json"
 # Final custody may use the reserved 60s, but never a new absolute deadline.
 now=$(date -u +%s);left=$((LP_ABSOLUTE_DEADLINE_EPOCH - now));cap=55
 if (( left > 0 ));then
  (( left >= cap )) || cap=$left
  timeout --signal=TERM --kill-after=3s "$cap" aws --region us-east-2 s3 sync \
    "$out/" "$ISOLAB_RESULTS_URI" --only-show-errors > "$out/final-upload.stdout" 2> "$out/final-upload.stderr"
  upload=$?
 else upload=125
 fi
 printf '%s\n' "$upload" > "$out/final-upload.exit"
 # Upload the completed upload receipt separately; it cannot attest to itself.
 if (( upload == 0 ));then
  now=$(date -u +%s);left=$((LP_ABSOLUTE_DEADLINE_EPOCH - now))
  if (( left > 0 ));then
   timeout --signal=TERM --kill-after=1s "$left" aws --region us-east-2 s3 cp \
    "$out/final-upload.exit" "${ISOLAB_RESULTS_URI}final-upload.exit" --only-show-errors || upload=91
  else upload=125
  fi
 fi
 (( original == 0 )) || exit "$original"
 (( upload == 0 )) || exit 91
 exit 0
}
trap finish EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

# Every exact command, whole output, exit and time/RSS log is retained. A
# timeout, signal, missing fixture or failed upload never counts as rejection.
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
 sync_results
}
helper() { phase "$1" 120 0 "${@:2}"; }
native() { phase "$1" 900 0 "${@:2}"; }
reject() { phase "$1" 900 1 "${@:2}"; }
replay_footer() {
 jq --exit-status --slurp 'length==61 and .[-1]=={record:"complete",call_count:60,matrix_certificate_count:240,replay:"complete"}' "$1"
}
no_accepted_footer() { jq --exit-status --slurp 'all(.[]; .record!="complete")' "$1"; }

helper initial-original1605-source-guard sha256sum --check experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256
helper initial-pure50-source-guard sha256sum --check "$component/historical-01/source-01.sha256"
helper initial-population-runtime-source-guard sha256sum --check "$component/population-01/source-01.sha256"
helper retain-all-inputs cp -R --preserve=mode,timestamps "$inputs" "$out/entire-original-inputs"
helper retain-entire-original-runtime cp -R --preserve=mode,timestamps "$capsule" "$out/entire-original-runtime-capsule"
helper retain-entire-new-native-build cp -R --preserve=mode,timestamps "$bins" "$out/entire-new-native-build"
inputs=$out/entire-original-inputs
bins=$out/entire-new-native-build
capsule=$out/entire-original-runtime-capsule
helper original-whole-capsule-archive bash -c 'printf "%s  %s\n" "$(jq -r .original_archive.sha256 "$1")" "$2" | sha256sum --check' _ \
 "$pkg/runtime-01/manifest-01.json" "$capsule/entire-original-artifact.zip"
helper original-all56-selected-members bash -c 'cd "$1" && exec sha256sum --check "$2"' _ \
 "$capsule/entire-original-members-used" "$pkg/runtime-01/selected-members-01.sha256"
for label in rank-replay character-auditor;do
 name=original-rank-replayer;[[ $label == rank-replay ]] || name=original-character-auditor
 helper "$label-unchanged-native" cmp "$capsule/native/$name" \
  "$capsule/entire-original-members-used/n4-original-relation-output/actual-runtime-$label.bin"
done
helper exact-new-build-native-pins bash -c 'cd "$1" && exec sha256sum --check binary-pins.sha256' _ "$bins"
helper exact-new-build-source jq --exit-status --arg source "$expected" '.source_revision==$source and .scope=="new pure source compilation; original baseline reuse separate"' "$bins/build-receipt.json"

# Use the unchanged original gate. Any pre-existing assigned credential/profile
# is configured externally; no identity, token or grant is created by this file.
helper original-checkpoint-gate bash scripts/checkpoint.sh gate
helper retain-genuine-original-checkpoint-receipt cp .resume/.last-push "$out/original-last-push.txt"
read -r state_hash stamp checkpoint_uri < "$out/original-last-push.txt"
[[ $state_hash =~ ^[0-9a-f]{64}$ && $stamp =~ ^[A-Za-z0-9._=-]+$ ]]
[[ $checkpoint_uri == s3://setec-astronomy-artifacts/checkpoints/cryptanalysis/*/"$stamp"/ \
 || $checkpoint_uri == "${ISOLAB_RESULTS_URI}checkpoints/cryptanalysis/"*/"$stamp"/ ]]
helper original-entire-checkpoint-readback aws --region "${CHECKPOINT_AWS_REGION:-us-east-2}" s3 cp --only-show-errors \
 "${checkpoint_uri}checkpoint.tar.gz" "$out/remote-checkpoint.tar.gz"
helper original-entire-resume-readback aws --region "${CHECKPOINT_AWS_REGION:-us-east-2}" s3 cp --only-show-errors \
 "${checkpoint_uri}RESUME.md" "$out/remote-RESUME.md"
helper original-entire-meta-readback aws --region "${CHECKPOINT_AWS_REGION:-us-east-2}" s3 cp --only-show-errors \
 "${checkpoint_uri}meta.json" "$out/remote-meta.json"
helper original-entire-resume-equality cmp .resume/RESUME.md "$out/remote-RESUME.md"
helper original-exact-checkpoint-source jq --exit-status --arg source "$expected" \
 '.head==$source and .repo=="cryptanalysis"' "$out/remote-meta.json"
helper original-checkpoint-member-list tar -tzf "$out/remote-checkpoint.tar.gz"
helper original-checkpoint-pack-resume bash -c 'tar -xOzf "$1" ./RESUME.md > "$2"' _ "$out/remote-checkpoint.tar.gz" "$out/pack-RESUME.md"
helper original-checkpoint-pack-meta bash -c 'tar -xOzf "$1" ./meta.json > "$2"' _ "$out/remote-checkpoint.tar.gz" "$out/pack-meta.json"
helper original-pack-resume-equality cmp "$out/pack-RESUME.md" "$out/remote-RESUME.md"
helper original-pack-meta-equality cmp "$out/pack-meta.json" "$out/remote-meta.json"

trace=$inputs/passive-whole60-trace.json
capture=$inputs/historical-passive-acceptance-01.json
witnesses=$inputs/source-character-whole60-witnesses.jsonl
old_certs=$inputs/relation-whole60-certificates.jsonl
public=$out/entire-primary-public.jsonl
cert=$out/entire-primary-certificates.jsonl
replayer=$bins/historical_certificates
native all-six-whole-original-fixture-pins "$bins/lp-post-character" --check-fixtures "$inputs" "$capture" "$out/whole-input-byte-pins.json"
native strict-primary-extraction "$bins/extract_public" --primary "$trace" "$public"
native public-only-full-production "$replayer" produce "$public" "$cert"
native independent-full-primary-replay "$replayer" replay-primary "$trace" "$public" "$cert" "$out/entire-primary-replay.jsonl"
helper require-entire-primary-completion replay_footer "$out/entire-primary-replay.jsonl"
for kind in operation kernel a-basis zero-projection full-lift;do
 modified=$out/entire-$kind-control.jsonl
 rejected=$out/entire-$kind-rejected-replay.jsonl
 native "construct-full-$kind-control" "$replayer" tamper-certificate "$kind" "$cert" "$modified"
 reject "reject-full-$kind-control" "$replayer" replay-primary "$trace" "$public" "$modified" "$rejected"
 helper "no-accepted-$kind-footer" no_accepted_footer "$rejected"
done
for kind in raw-graph oracle;do
 modified=$out/entire-$kind-public-control.jsonl
 rejected=$out/entire-$kind-rejected-replay.jsonl
 native "construct-full-$kind-control" "$replayer" tamper-public "$kind" "$public" "$modified"
 reject "reject-full-$kind-control" "$replayer" replay-primary "$trace" "$modified" "$cert" "$rejected"
 helper "no-accepted-$kind-footer" no_accepted_footer "$rejected"
done
feedback=$out/entire-feedback-canary-trace.json
feedback_public=$out/entire-feedback-public.jsonl
feedback_cert=$out/entire-feedback-certificates.jsonl
native whole-private-feedback-copy "$replayer" feedback-copy "$trace" "$feedback"
native strict-feedback-extraction "$bins/extract_public" --feedback-control "$trace" "$feedback" "$feedback_public"
native full-feedback-production "$replayer" produce "$feedback_public" "$feedback_cert"
native independent-full-feedback-replay "$replayer" replay-feedback "$trace" "$feedback" "$feedback_public" "$feedback_cert" "$out/entire-feedback-replay.jsonl"
helper require-entire-feedback-completion replay_footer "$out/entire-feedback-replay.jsonl"
native exact-whole-scientific-feedback-invariance "$replayer" compare-feedback "$cert" "$feedback_cert"

native unchanged-original360-replay "$capsule/native/original-rank-replayer" "$trace" "$capture" "$old_certs" "$out/entire-fresh-original360-verdict.json"
helper entire-original360-verdict-equality cmp "$out/entire-fresh-original360-verdict.json" "$inputs/relation-whole60-verdict.json"
native unchanged-actual-norm-witness-auditor "$capsule/native/original-character-auditor" "$trace" \
 "$out/entire-fresh-original360-verdict.json" "$witnesses" "$out/entire-fresh-original-character-verdict.json"
helper entire-original-witness-verdict-equality cmp "$out/entire-fresh-original-character-verdict.json" "$inputs/source-character-whole60-verdict.json"
native separate-full-post-character-audit "$bins/lp-post-character" "$trace" "$public" "$cert" "$witnesses" \
 "$out/entire-fresh-original360-verdict.json" "$out/entire-fresh-original-character-verdict.json" "$out/entire-post-character-verdict.jsonl"
helper require-entire-post-completion jq --exit-status --slurp \
 'length==62 and .[-1].record=="complete" and .[-1].call_count==60 and .[-1].matrix_certificate_count==240' "$out/entire-post-character-verdict.jsonl"
native final-all-six-whole-fixture-pins "$bins/lp-post-character" --check-fixtures "$inputs" "$capture" "$out/final-whole-input-byte-pins.json"
helper final-exact-new-native-pins bash -c 'cd "$1" && exec sha256sum --check binary-pins.sha256' _ "$bins"
helper final-all56-original-selected-members bash -c 'cd "$1" && exec sha256sum --check "$2"' _ \
 "$capsule/entire-original-members-used" "$pkg/runtime-01/selected-members-01.sha256"
helper final-population-runtime-source-guard sha256sum --check "$component/population-01/source-01.sha256"
helper final-original1605-source-guard sha256sum --check experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256
helper final-pure50-source-guard sha256sum --check "$component/historical-01/source-01.sha256"
helper final-original-checkpoint-status bash scripts/checkpoint.sh status
[[ -z $(git status --porcelain --untracked-files=all) ]]
complete=true
