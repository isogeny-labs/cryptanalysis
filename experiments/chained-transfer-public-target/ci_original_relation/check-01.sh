#!/usr/bin/env bash
# Whole diagnostic replay after the separately pinned complete comparator03 controls.
# All mathematical producers, replays and controls are native Rust/Lean.
set -euo pipefail
[[ $# == 3 ]] || exit 2
ci=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$ci" rev-parse --show-toplevel)
producer=$(cd -- "$1" && pwd -P)
out=$(realpath -m "$2")
checkpoint=$(realpath -m "$3")
[[ -d $checkpoint && $(cat "$checkpoint/source-head.txt") == "$(git -C "$ci" rev-parse HEAD)" ]] || exit 2
[[ ! -e $out && $(realpath -m "$repo/../crypto") == "$producer" ]] || exit 2
case "$out/" in "$repo/"*|"$producer/"*) exit 2;; esac
study=experiments/chained-transfer-public-target
[[ $(git -C "$producer" rev-parse HEAD) == "$(cat "$repo/$study/upstream-commit.txt")" ]] || exit 2
for tool in cargo rustc lean lake python3 jq xz tar;do command -v "$tool" >/dev/null || exit 2;done
mkdir "$out"
export RUSTUP_TOOLCHAIN=1.99.1
reference=$ci/reference-01.sha256
cp "$reference" "$out/original-reference.sha256"
cp "$ci/phase-plan-01.txt" "$out/original-phase-plan.txt"
cp "$0" "$out/original-command.sh"
phase(){
 local name=$1 expected=$2;shift 2
 set +e
 "$@" 2>&1 | tee "$out/$name.txt"
 local codes=("${PIPESTATUS[@]}")
 set -e
 printf '%s %s\n' "${codes[0]}" "${codes[1]}" > "$out/$name.pipe-exits"
 printf '%s %s %s\n' "$name" "$expected" "${codes[0]}" >> "$out/phases.txt"
 [[ ${codes[0]} == "$expected" && ${codes[1]} == 0 ]]
}
bounded(){ (ulimit -v 2097152;exec timeout 900 "$@"); }
helper(){ (ulimit -v 2097152;exec timeout 120 "$@"); }
finish(){
 local code=$?;trap - EXIT;set +e
 sha256sum --check "$reference" > "$out/final-source-guards.txt" 2>&1
 local guard=$?
 cmp "$reference" "$out/original-reference.sha256" >> "$out/final-source-guards.txt" 2>&1 || guard=1
 printf '%s\n' "$guard" > "$out/final-source-guards.exit"
 [[ $code != 0 || $guard == 0 ]] || code=$guard
 printf '%s\n' "$code" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 exit "$code"
}
trap finish EXIT
cd "$repo"
date -u +%FT%TZ > "$out/start.txt"
git rev-parse HEAD > "$out/consumer-head.txt"
git -C "$producer" rev-parse HEAD > "$out/producer-head.txt"
rustc -Vv > "$out/rustc.txt"
cp -a "$checkpoint" "$out/original-pre-native-checkpoint"
phase immediate-original-checkpoint-gate 0 timeout 120 bash scripts/checkpoint.sh gate
phase initial-published-source-guards 0 sha256sum --check "$reference"
phase initial-comparator-source-guards 0 sha256sum --check "$ci/frozen-comparator-inputs-03.sha256"

# Preserve the entire already accepted original CI and its only engine setup.
legacy=$out/inherited-original-fixed-ic
phase inherited-whole-original-IC-and-sampler 0 bash "$repo/$study/ci_original_fixed_ic/check-01.sh" "$producer" "$legacy"
[[ $(cat "$legacy/original.exit") == 0 ]]
export CARGO_TARGET_DIR=${legacy}-build-cache
cp "$legacy/engine-prepared.json" "$out/engine-prepared.json"
cp "$legacy/chain-metadata.txt" "$out/chain-metadata.txt"
base_ci=$repo/$study/ci_fixed_chain
for package in original-relation-kernel-01 original-relation-rank-01 original-relation-character-01 ci_original_relation/audit-03;do
 label=${package//\//-}
 phase "fetch-$label" 0 timeout 120 cargo fetch --locked --manifest-path "$repo/$study/$package/Cargo.toml"
 mkdir -p "$out/actual-compiled-source/$package"
 cp -aL "$repo/$study/$package/." "$out/actual-compiled-source/$package/"
done
passive=$repo/$study/original-relation-kernel-01
rank=$repo/$study/original-relation-rank-01
character=$repo/$study/original-relation-character-01
bundle=$out/whole-fresh-bundle
mkdir "$bundle"
cp "$legacy/original-ic-expected.json" "$bundle/original-baseline.json"
phase passive-prior1532-compatible 0 sha256sum --check "$character/frozen-prior-inputs-01.sha256"
phase passive-current17 0 sha256sum --check "$passive/frozen-current-inputs-01.sha256"
phase passive-metadata 0 timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$passive/Cargo.toml"
phase passive-engine-closure 0 python3 "$base_ci/engine_closure_03.py" "$out" "$producer" passive
phase passive-compile 0 timeout 120 cargo test --release --locked --offline --manifest-path "$passive/Cargo.toml" --lib --no-run --message-format=json
python3 "$base_ci/capture_executable.py" "$out" passive compiled
python3 "$base_ci/capture_engine.py" "$out" "$producer" reused passive
for spec in passive-auditor:audit-original-relation-trace passive-native-auditor:audit-original-relation-native-records;do
 label=${spec%%:*};bin=${spec#*:}
 phase "$label-compile" 0 timeout 120 cargo build --release --locked --offline --manifest-path "$passive/Cargo.toml" --bin "$bin" --message-format=json
 python3 "$base_ci/capture_auditor.py" "$out" compiled "$label" "$bin"
done
export N4_RELATION_TRACE_OUTPUT=$bundle/passive-whole60-trace.json
phase passive-native 0 bounded cargo test --release --locked --offline --manifest-path "$passive/Cargo.toml" --lib -- --nocapture --test-threads=1
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/passive-native.txt"
python3 "$base_ci/capture_executable.py" "$out" passive runtime
python3 "$base_ci/capture_engine.py" "$out" "$producer" reused passive
ln "$out/passive-native.txt" "$bundle/native.txt"
mv "$bundle/passive-whole60-trace.journal.jsonl" "$bundle/journal.jsonl"
native_auditor=$(cat "$out/passive-native-auditor-actual-path.txt")
passive_auditor=$(cat "$out/passive-auditor-actual-path.txt")
phase passive-whole100-freeze 0 helper "$native_auditor" --freeze "$bundle/native.txt" "$bundle/passive-whole100-native.json"
phase passive-whole100-same-run-compare 0 helper "$native_auditor" --compare "$bundle/passive-whole100-native.json" "$bundle/native.txt" "$out/passive-whole100-same-run-compared.json"
phase passive-freeze-compared-bytes 0 cmp "$bundle/passive-whole100-native.json" "$out/passive-whole100-same-run-compared.json"
phase passive-whole60-original-parity-and660journal 0 bounded "$passive_auditor" --audit "$bundle/original-baseline.json" "$bundle/native.txt" "$bundle/passive-whole60-trace.json" "$bundle/journal.jsonl" "$bundle/passive-acceptance.json"
for stage in available selected candidate descent;do
 omitted=$out/passive-$stage-entire-stage-omitted.json.xz
 phase "passive-$stage-materialize-whole-omission" 0 timeout 120 python3 "$passive/omit_capture_stage.py" "$bundle/passive-whole60-trace.json" "$stage" "$omitted"
 phase "passive-$stage-whole-omission-CRC" 0 timeout 120 xz --test "$omitted"
 phase "passive-$stage-rejection" 101 bash -c 'exec timeout 120 "$1" --audit "$2" "$3" <(xz -dc "$4") "$5" "$6"' _ "$passive_auditor" "$bundle/original-baseline.json" "$bundle/native.txt" "$omitted" "$bundle/journal.jsonl" "$out/passive-$stage-must-not-accept.json"
 [[ ! -e $out/passive-$stage-must-not-accept.json ]]
done
for spec in passive-auditor:audit-original-relation-trace passive-native-auditor:audit-original-relation-native-records;do
 python3 "$base_ci/capture_auditor.py" "$out" runtime "${spec%%:*}" "${spec#*:}"
done

# Serde-only exact rank tools: preserve separate full no-engine metadata.
mkdir "$out/rank-no-field-engine"
phase rank-current10 0 sha256sum --check "$rank/frozen-current-inputs-01.sha256"
phase rank-metadata 0 timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$rank/Cargo.toml"
cp "$out/rank-metadata.txt" "$out/rank-no-field-engine/original-kernel-metadata.txt"
phase rank-no-field-engine-closure 0 python3 "$base_ci/engine_closure_03.py" "$out/rank-no-field-engine" "$producer" original-kernel
for spec in rank-producer:produce-original-relation-ranks rank-replay:replay-original-relation-ranks rank-controls:controls;do
 label=${spec%%:*};bin=${spec#*:}
 phase "$label-compile" 0 timeout 120 cargo build --release --locked --offline --manifest-path "$rank/Cargo.toml" --bin "$bin" --message-format=json
 python3 "$base_ci/capture_auditor.py" "$out" compiled "$label" "$bin"
done
rp=$(cat "$out/rank-producer-actual-path.txt");rr=$(cat "$out/rank-replay-actual-path.txt");rc=$(cat "$out/rank-controls-actual-path.txt")
trace=$bundle/passive-whole60-trace.json
capture=$bundle/passive-acceptance.json
cert=$bundle/relation-whole60-certificates.jsonl
rv=$bundle/relation-whole60-verdict.json
phase rank-produce-all360-certificates 0 bounded "$rp" "$trace" "$capture" "$cert"
phase rank-independent-all360-replay 0 bounded "$rr" "$trace" "$capture" "$cert" "$rv"
phase rank-materialize-both-whole-controls 0 helper "$rc" "$cert" "$out/whole-matrix-coefficient-modified.jsonl" "$out/whole-constrained-kernel-modified.jsonl"
for name in matrix-coefficient constrained-kernel;do
 phase "rank-$name-rejection" 101 bounded "$rr" "$trace" "$capture" "$out/whole-$name-modified.jsonl" "$out/$name-must-not-accept.json"
 [[ ! -e $out/$name-must-not-accept.json ]]
done
for spec in rank-producer:produce-original-relation-ranks rank-replay:replay-original-relation-ranks rank-controls:controls;do
 python3 "$base_ci/capture_auditor.py" "$out" runtime "${spec%%:*}" "${spec#*:}"
done

phase character-current11 0 sha256sum --check "$character/frozen-current-inputs-01.sha256"
phase character-metadata 0 timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$character/Cargo.toml"
phase character-engine-closure 0 python3 "$base_ci/engine_closure_03.py" "$out" "$producer" character
for spec in character-producer:produce-original-source-character character-auditor:audit-original-source-character character-mutation:mutate-original-source-character;do
 label=${spec%%:*};bin=${spec#*:}
 phase "$label-compile" 0 timeout 120 cargo build --release --locked --offline --manifest-path "$character/Cargo.toml" --bin "$bin" --message-format=json
 python3 "$base_ci/capture_auditor.py" "$out" compiled "$label" "$bin"
 python3 "$base_ci/capture_engine.py" "$out" "$producer" reused "$label"
done
character_producer=$(cat "$out/character-producer-actual-path.txt");ca=$(cat "$out/character-auditor-actual-path.txt");cm=$(cat "$out/character-mutation-actual-path.txt")
witness=$bundle/source-character-whole60-witnesses.jsonl
cv=$bundle/source-character-whole60-verdict.json
phase character-generate-entire60-witnesses 0 bounded "$character_producer" "$trace" "$rv" "$witness"
phase character-independent-entire60-direct-source-audit 0 bounded "$ca" "$trace" "$rv" "$witness" "$cv"
phase character-materialize-whole-scalar-mutation 0 helper "$cm" "$witness" "$out/whole-character-scalar-modified.jsonl"
phase character-direct-source-scalar-rejection 101 bounded "$ca" "$trace" "$rv" "$out/whole-character-scalar-modified.jsonl" "$out/character-scalar-must-not-accept.json"
[[ ! -e $out/character-scalar-must-not-accept.json ]]
for spec in character-producer:produce-original-source-character character-auditor:audit-original-source-character character-mutation:mutate-original-source-character;do
 python3 "$base_ci/capture_auditor.py" "$out" runtime "${spec%%:*}" "${spec#*:}"
 python3 "$base_ci/capture_engine.py" "$out" "$producer" reused "${spec%%:*}"
done

# Complete strict historical comparison and every full fresh-side variation.
mkdir "$out/comparator-no-field-engine"
manifest=$ci/audit-03/Cargo.toml
phase comparator-metadata 0 timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$manifest"
cp "$out/comparator-metadata.txt" "$out/comparator-no-field-engine/original-kernel-metadata.txt"
phase comparator-no-field-engine-closure 0 python3 "$base_ci/engine_closure_03.py" "$out/comparator-no-field-engine" "$producer" original-kernel
phase comparator-compile 0 timeout 120 cargo build --release --locked --offline --manifest-path "$manifest" --bin audit-original-relation-historical-03 --message-format=json
python3 "$base_ci/capture_auditor.py" "$out" compiled comparator audit-original-relation-historical-03
phase comparator-original-hash-library-tests 0 timeout 120 cargo test --release --locked --offline --manifest-path "$manifest" --lib
cmp_tool=$(cat "$out/comparator-actual-path.txt")
pins=$ci/historical-whole-fixture-pins-01.json
docs=$repo/docs/research-artifacts/chained-transfer/original-relation-rank-character-27
hist_capture=$ci/historical-passive-acceptance-01.json
phase whole-strict-historical-positive 0 helper "$cmp_tool" --compare "$pins" "$docs" "$hist_capture" "$bundle" "$out/whole-strict-historical-accepted.json"
phase whole-historical-controls-materialize 0 helper "$cmp_tool" --controls "$bundle" "$out/whole-historical-controls"
for name in timing-only missing-record-class changed-counter changed-relation changed-kernel missing-rank-call changed-character-scalar unexpected-verdict-field unbound-linked-hash;do
 expected=1;[[ $name != timing-only ]] || expected=0
 phase "whole-historical-$name" "$expected" helper "$cmp_tool" --compare "$pins" "$docs" "$hist_capture" "$out/whole-historical-controls/$name" "$out/$name-historical-accepted.json"
 if [[ $expected == 1 ]];then [[ ! -e $out/$name-historical-accepted.json ]];else [[ -f $out/$name-historical-accepted.json ]];fi
done
python3 "$base_ci/capture_auditor.py" "$out" runtime comparator audit-original-relation-historical-03

# Retain full raw certificates and their lossless byte-checked compressed copies.
for file in "$cert" "$out/whole-matrix-coefficient-modified.jsonl" "$out/whole-constrained-kernel-modified.jsonl" "$witness" "$out/whole-character-scalar-modified.jsonl";do
 name=$(basename "$file")
 phase "whole-$name-XZ" 0 timeout 120 bash -c 'exec xz -T1 -1 -c "$1" > "$2"' _ "$file" "$file.xz"
 phase "whole-$name-CRC" 0 timeout 120 xz --test "$file.xz"
 phase "whole-$name-decoded-byte-equality" 0 timeout 120 bash -o pipefail -c 'xz -dc "$1" | cmp - "$2";codes=("${PIPESTATUS[@]}");printf "%s\n" "${codes[*]}";[[ ${codes[0]} == 0 && ${codes[1]} == 0 ]]' _ "$file.xz" "$file"
done
phase full-historical-controls-archive 0 timeout 120 bash -o pipefail -c 'tar -cf - -C "$1" . | xz -T1 -1 > "$2";codes=("${PIPESTATUS[@]}");printf "%s\n" "${codes[*]}";[[ ${codes[0]} == 0 && ${codes[1]} == 0 ]]' _ "$out/whole-historical-controls" "$out/whole-historical-controls.tar.xz"
phase full-historical-controls-archive-CRC 0 timeout 120 xz --test "$out/whole-historical-controls.tar.xz"
phase full-historical-controls-all-original-bytes 0 timeout 120 bash -o pipefail -c 'xz -dc "$1" | tar -df - -C "$2";codes=("${PIPESTATUS[@]}");printf "%s\n" "${codes[*]}";[[ ${codes[0]} == 0 && ${codes[1]} == 0 ]]' _ "$out/whole-historical-controls.tar.xz" "$out/whole-historical-controls"

mkdir -p "$producer/target"
stage=$(mktemp -d "$producer/target/original-relation-kernel-proof.XXXXXX")
module=$study/original-relation-rank-01/lean/RelationKernel.lean
cp "$repo/$module" "$stage/RelationKernel.lean"
cp -a "$stage" "$out/actual-kernel-proof-stage"
phase consumer-original27-declaration-kernel-gate 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash tools/lean/proof-gate.sh --out "$out/consumer-kernel-proofs" "$module"
phase producer-original27-declaration-kernel-gate 0 bash -c 'cd "$1";shift;exec env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash tools/lean/proof-gate.sh "$@"' _ "$producer" --out "$out/producer-kernel-proofs" "$stage/RelationKernel.lean"
while IFS= read -r claim;do
 phase "kernel-binding-$claim" 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 tools/pcc/pcc.py verify "pcc/claims/$claim.json" --json
done < "$ci/kernel-statement-bindings-01.txt"
phase complete-operational-receipt-validation 0 python3 "$ci/validate_receipts_01.py" "$repo" "$out"
phase final-published-source-guards 0 sha256sum --check "$reference"
