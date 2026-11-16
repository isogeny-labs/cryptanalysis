#!/usr/bin/env bash
# Build and retain actual bytes only; no mathematical test or auditor execution.
set -euo pipefail
[[ $# == 3 ]] || exit 2
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$pkg" rev-parse --show-toplevel)
producer=$(cd -- "$1" && pwd -P)
cache=$(realpath -m "$2")
out=$(realpath -m "$3")
[[ ! -e $out && -d $cache && $(realpath -m "$repo/../crypto") == "$producer" ]] || exit 2
mkdir "$out"
export PATH=/home/agent/.cargo/bin:/home/agent/.elan/bin:$PATH
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=$cache
cd "$repo"
finish(){ local status=$?; trap - EXIT; printf '%s\n' "$status" > "$out/original.exit"; date -u +%FT%TZ > "$out/finish.txt"; exit "$status"; }
trap finish EXIT
date -u +%FT%TZ > "$out/start.txt"
cp "$0" "$out/original-command.sh"
cp -aL "$pkg" "$out/actual-source"
phase(){
 local name=$1;shift
 set +e
 "$@" > "$out/$name.txt" 2> "$out/$name.stderr.txt"
 local status=$?
 set -e
 printf '%s\n' "$status" > "$out/$name.exit"
 [[ $status == 0 ]]
}
phase prior1028 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256"
phase metadata timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$pkg/Cargo.toml"
# Usually fresh in the declared identical warm cache. If Cargo actually needs
# a changed graph, this is the ONE explicitly bounded package preparation.
phase original-engine-preparation timeout 900 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --package isogeny_algos --lib --message-format=json
python3 "$pkg/capture_engine.py" "$out" "$producer" prepared
phase fourth-compile timeout 120 cargo test --release --locked --offline --manifest-path "$pkg/Cargo.toml" --lib --no-run --message-format=json
python3 "$repo/experiments/chained-transfer-public-target/ci_twisted_pair/capture_executable.py" "$out" fourth compiled
python3 "$pkg/capture_engine.py" "$out" "$producer" reused
for bin in audit-paired-fourth paired-fourth-old-dual-control; do
 phase "$bin-compile" timeout 120 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --bin "$bin" --message-format=json
 python3 - "$out" "$bin" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
out=Path(sys.argv[1]);name=sys.argv[2];rows=[]
for line in(out/(name+'-compile.txt')).read_text().splitlines():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 if r.get('reason')=='compiler-artifact'and r.get('target',{}).get('name')==name:rows.append(r)
assert len(rows)==1
r=rows[0];p=Path(r['executable']);q=out/(name+'.actual-compiled.bin');shutil.copy2(p,q)
(out/(name+'-executable.json')).write_text(json.dumps(dict(actual_Cargo_artifact=r,actual_path=str(p),actual_copy=str(q),bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),scope='compiled only; not executed'),indent=2)+'\n')
PY
done
phase final-prior1028 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256"
