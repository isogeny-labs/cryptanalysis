#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct80-observer-storage-build-02-cache
layout=/workspace/scratch/ct80-observer-storage-layout-02/derived-layout
out=/workspace/scratch/ct80-observer-storage-build-02
manifest=$layout/norm-census/Cargo.toml
[[ ! -e $out && ! -e $CARGO_TARGET_DIR ]] || exit 2
mkdir "$out"
cp "$0" "$out/original-command.sh"
cp /workspace/cryptanalysis/experiments/chained-transfer-public-target/ci_nondual_preflight/capture_engine.py "$out/original-capture-engine.py"
sed 's/second-edge-compile.txt/observer-compile.txt/' "$out/original-capture-engine.py" > "$out/capture-observer-engine.py"
cargo generate-lockfile --offline --manifest-path "$manifest" > "$out/lock.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/lock.exit"
[[ $status == 0 ]] || exit "$status"
cp "$layout/norm-census/Cargo.lock" "$out/actual-Cargo.lock"
timeout 900 cargo build --release --locked --offline --manifest-path "$manifest" --package isogeny_algos --message-format=json > "$out/original-engine-preparation.txt" 2> "$out/original-engine-preparation.stderr.txt"
status=$?
printf '%s\n' "$status" > "$out/original-engine-preparation.exit"
[[ $status == 0 ]] || exit "$status"
python3 "$out/capture-observer-engine.py" "$out" "$layout/crypto" prepared > "$out/engine-prepared-caller.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/engine-prepared-caller.exit"
[[ $status == 0 ]] || exit "$status"
timeout 120 cargo build --release --locked --offline --manifest-path "$manifest" --bins --message-format=json > "$out/observer-compile.txt" 2> "$out/observer-compile.stderr.txt"
status=$?
printf '%s\n' "$status" > "$out/observer-compile.exit"
[[ $status == 0 ]] || exit "$status"
python3 - "$out" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
o=Path(sys.argv[1]);rows=[json.loads(x) for x in(o/'observer-compile.txt').read_text().splitlines()]; records=[]
for x in rows:
 if x.get('reason')=='compiler-artifact' and x.get('executable'):
  p=Path(x['executable']);q=o/(x['target']['name']+'.bin');shutil.copyfile(p,q)
  records.append(dict(Cargo_artifact=x,actual_copy=str(q),bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest()))
assert len(records)==3
(o/'actual-executables.json').write_text(json.dumps(records,indent=2)+'\n')
PY
status=$?
printf '%s\n' "$status" > "$out/executable-custody.exit"
[[ $status == 0 ]] || exit "$status"
python3 "$out/capture-observer-engine.py" "$out" "$layout/crypto" reused > "$out/engine-reused-caller.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/engine-reused-caller.exit"
exit "$status"
