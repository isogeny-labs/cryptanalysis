#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct80-twisted-pair-build-01-cache
pkg=/workspace/cryptanalysis/experiments/chained-transfer-public-target/twisted-pair-preflight
out=/workspace/scratch/ct80-twisted-pair-build-02
[[ ! -e $out && -e $CARGO_TARGET_DIR ]] || exit 2
mkdir "$out"
trap 'status=$?; printf "%s\n" "$status" > "$out/orchestrator.exit"; date -u +%FT%TZ > "$out/finish.txt"' EXIT
cp "$0" "$out/original-command.sh"
date -u +%FT%TZ > "$out/start.txt"
cp -a "$pkg" "$out/actual-source"
cp /workspace/cryptanalysis/experiments/chained-transfer-public-target/ci_nondual_preflight/capture_engine.py "$out/original-capture-engine.py"
sed 's/second-edge-compile.txt/twist-test-compile.jsonl/' "$out/original-capture-engine.py" > "$out/capture-twist-engine.py"
sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" > "$out/prior981.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/prior981.exit"
[[ $status == 0 ]] || exit "$status"
cargo metadata --offline --locked --format-version 1 --manifest-path "$pkg/Cargo.toml" > "$out/metadata.json" 2> "$out/metadata.stderr.txt"
status=$?
printf '%s\n' "$status" > "$out/metadata.exit"
[[ $status == 0 ]] || exit "$status"
cp /workspace/scratch/ct80-twisted-pair-build-01/engine-prepared.json "$out/engine-prepared.json"
cp /workspace/scratch/ct80-twisted-pair-build-01/original-engine-preparation.exit "$out/prior-original-engine-preparation.exit"
printf '%s\n' 'Same original unchanged prepared engine/cache from build01; no second preparation, only degree13 forward-helper call corrected.' > "$out/correction-scope.txt"
timeout 120 cargo test --release --offline --locked --manifest-path "$pkg/Cargo.toml" --lib --no-run --message-format=json > "$out/twist-test-compile.jsonl" 2> "$out/twist-test-compile.stderr.txt"
status=$?
printf '%s\n' "$status" > "$out/twist-test-compile.exit"
[[ $status == 0 ]] || exit "$status"
python3 - "$out" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
o=Path(sys.argv[1]);rows=[json.loads(x) for x in(o/'twist-test-compile.jsonl').read_text().splitlines()];tests=[x for x in rows if x.get('reason')=='compiler-artifact' and x.get('executable')];assert len(tests)==1
x=tests[0];p=Path(x['executable']);q=o/'actual-test-executable.bin';shutil.copy2(p,q);(o/'actual-test-executable.json').write_text(json.dumps(dict(Cargo_artifact=x,actual_copy=str(q),bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest()),indent=2)+'\n')
PY
status=$?
printf '%s\n' "$status" > "$out/test-executable-custody.exit"
[[ $status == 0 ]] || exit "$status"
python3 "$out/capture-twist-engine.py" "$out" /workspace/crypto reused > "$out/reused-custody.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/reused-custody.exit"
[[ $status == 0 ]] || exit "$status"
timeout 120 cargo build --release --offline --locked --manifest-path "$pkg/Cargo.toml" --bin audit-twisted-pair --message-format=json > "$out/auditor-compile.jsonl" 2> "$out/auditor-compile.stderr.txt"
status=$?
printf '%s\n' "$status" > "$out/auditor-compile.exit"
[[ $status == 0 ]] || exit "$status"
python3 - "$out" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
o=Path(sys.argv[1]);rows=[json.loads(x) for x in(o/'auditor-compile.jsonl').read_text().splitlines()];bins=[x for x in rows if x.get('reason')=='compiler-artifact' and x.get('executable')];assert len(bins)==1
x=bins[0];p=Path(x['executable']);q=o/'actual-auditor-executable.bin';shutil.copy2(p,q);(o/'actual-auditor-executable.json').write_text(json.dumps(dict(Cargo_artifact=x,actual_copy=str(q),bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest()),indent=2)+'\n')
PY
status=$?
printf '%s\n' "$status" > "$out/auditor-executable-custody.exit"
[[ $status == 0 ]] || exit "$status"
sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" > "$out/final-prior981.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/final-prior981.exit"
exit "$status"
