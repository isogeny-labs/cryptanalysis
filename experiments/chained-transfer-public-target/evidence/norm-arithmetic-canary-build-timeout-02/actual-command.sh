#!/usr/bin/env bash
# Paired copies, one actual coefficient hook omitted, arithmetic bytes preserved.
set -euo pipefail
[[ $# == 2 && -n ${CARGO_TARGET_DIR:-} ]] || exit 2
layout=$(cd -- "$1" && pwd -P)
out=$(realpath -m "$2")
[[ ! -e $out ]] || exit 2
backend=$layout/derived-layout/crypto/isogeny_algos
taps=$layout/derived-layout/n4-arithmetic-taps
source=$layout/derived-layout/cryptanalysis/experiments/chained-transfer-public-target/beta-rational-lift/quadratic-picard-engine/src/lib.rs
mkdir -p "$out/positive/src" "$out/negative/src"
for arm in positive negative; do
 cat > "$out/$arm/Cargo.toml" <<TOML
[package]
name = "norm-qpic-$arm-hook-control"
version = "0.1.0"
edition = "2021"
publish = false
[workspace]
[features]
arithmetic-audit-controls = []
[dependencies]
isogeny_algos = { path = "$backend" }
n4-arithmetic-taps = { path = "$taps" }
serde_json = "=1.0.145"
TOML
 python3 - "$source" "$out/$arm/src/lib.rs" <<'SLICES'
from pathlib import Path
import hashlib,json,sys
s=Path(sys.argv[1]).read_text();first=s[s.index('struct Fq {'):s.index('/// A subspace of')];start=s.index('impl Fq {\n    fn sub_nc');second=s[start:s.index('/// Is `q` an odd prime',start)];start=s.index('#[cfg(feature = "arithmetic-audit-controls")]');controls=s[start:];body='use std::cell::Cell;\n'+first+second+controls;Path(sys.argv[2]).write_text(body);Path(sys.argv[2]+'.slices.json').write_text(json.dumps({'source':sys.argv[1],'whole_source_sha256':hashlib.sha256(s.encode()).hexdigest(),'literal_slices':[{'bytes':len(v.encode()),'sha256':hashlib.sha256(v.encode()).hexdigest()}for v in[first,second,controls]],'only_added_prefix':'use std::cell::Cell;','arithmetic_slices_unchanged':True},indent=2)+'\n')
SLICES
done
python3 - "$out" <<'PY'
from pathlib import Path
import hashlib,json,sys
p=Path(sys.argv[1]);s=(p/'positive/src/lib.rs').read_text();needle='        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "mul", 5);\n';assert s.count(needle)==1;n=s.replace(needle,'');(p/'negative/src/lib.rs').write_text(n)
(p/'source-omission.json').write_text(json.dumps({'actual_omitted_string':needle,'sites':1,'positive_sha256':hashlib.sha256(s.encode()).hexdigest(),'negative_sha256':hashlib.sha256(n.encode()).hexdigest(),'only_change':True},indent=2)+'\n')
PY
for arm in positive negative; do
 cargo generate-lockfile --offline --manifest-path "$out/$arm/Cargo.toml" > "$out/$arm-lock.txt" 2>&1
 set +e
 timeout 120 cargo test --release --offline --locked --features arithmetic-audit-controls --manifest-path "$out/$arm/Cargo.toml" --lib --no-run > "$out/$arm-build.txt" 2>&1
 build=$?
 set -e
 printf '%s\n' "$build" > "$out/$arm-build.exit"
 [[ $build == 0 ]] || exit "$build"
 set +e
 (ulimit -v 2097152; exec timeout 120 env N4_ARITHMETIC_OBSERVER=enabled cargo test --release --offline --locked --features arithmetic-audit-controls --manifest-path "$out/$arm/Cargo.toml" --lib -- --nocapture --test-threads=1) > "$out/$arm-native.txt" 2>&1
 status=$?
 set -e
 printf '%s\n' "$status" > "$out/$arm-native.exit"
 expected=0; [[ $arm == positive ]] || expected=101
 [[ $status == "$expected" ]] || exit 1
 grep -F '"all_algebra_equal":true' "$out/$arm-native.txt" >/dev/null
 if [[ $arm == positive ]]; then
  grep -F '"observed_coefficient_mul":5' "$out/$arm-native.txt" >/dev/null
  grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/$arm-native.txt"
 else
  grep -F '"observed_coefficient_mul":0' "$out/$arm-native.txt" >/dev/null
  grep -F 'actual omitted quadratic coefficient hook must reject' "$out/$arm-native.txt" >/dev/null
 fi
done
printf '0\n' > "$out/original.exit"
echo 'Actual omitted quadratic hook rejects101 after identical original-reference algebra; positive unfiltered primitive suite0.'
