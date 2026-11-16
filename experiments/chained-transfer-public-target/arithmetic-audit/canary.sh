#!/usr/bin/env bash
# Native primitive controls on two copied FpR sources; no source tree is edited.
set -euo pipefail
[[ $# == 2 && -n ${CARGO_TARGET_DIR:-} ]] || exit 2
layout=$(cd -- "$1" && pwd -P)
out=$(realpath -m "$2")
[[ ! -e $out && -d $layout/derived-layout/n4-arithmetic-taps ]] || exit 2
case "$out/" in "$layout/"*|"$CARGO_TARGET_DIR/"*) exit 2;; esac
mkdir -p "$out/positive/src" "$out/negative/src"
backend=$layout/derived-layout/crypto/isogeny_algos
taps=$layout/derived-layout/n4-arithmetic-taps
for arm in positive negative; do
 cat > "$out/$arm/Cargo.toml" <<TOML
[package]
name = "n4-arithmetic-$arm-hook-control"
version = "0.1.0"
edition = "2021"
publish = false
[workspace]
[dependencies]
isogeny_algos = { path = "$backend" }
n4-arithmetic-taps = { path = "$taps" }
serde_json = "=1.0.145"
serde = { version = "=1.0.228", features = ["derive"] }
TOML
 cp "$backend/src/fpr.rs" "$out/$arm/src/fpr.rs"
 cat > "$out/$arm/src/main.rs" <<'RUST'
//! Probe the actual copied coefficient hook; original FpR supplies the algebra check.
pub use isogeny_algos::{bigint,field,fpm,poly};
#[path="fpr.rs"] mod copied_fpr;
use field::Field;
fn main() {
 let f=copied_fpr::FpR::from_modulus(223,&[220,0,0,1]);
 let original=isogeny_algos::arithmetic_audit_original_fpr::FpR::from_modulus(223,&[220,0,0,1]);
 let mut a=[0;16];a[..3].fill(1);
 let result=n4_arithmetic_taps::within("omission-probe",||f.mul(a,a));
 let reference=original.mul(a,a);
 assert_eq!(result,reference,"original algebra must agree before checking counts");
 let actual=n4_arithmetic_taps::count("omission-probe","FpR.coefficient",223,"mul");
 println!("N4_ARITHMETIC_HOOK_PROBE {}",serde_json::json!({"manifest_dir":env!("CARGO_MANIFEST_DIR"),"all_algebra_equal":true,"result":result,"original_result":reference,"observed_mul":actual,"expected_mul":11}));
 assert_eq!(actual,11,"analytic coefficient-count control must detect a missing hook");
}
RUST
done
sed '/for j in 0\.\.r {/,/if self\.lazy {/s/n4_arithmetic_taps::hit("FpR\.coefficient", self\.p, "mul", 1); //' "$out/positive/src/fpr.rs" > "$out/negative/src/fpr.rs"
needle='n4_arithmetic_taps::hit("FpR.coefficient", self.p, "mul", 1);'
positive=$(grep -F -c "$needle" "$out/positive/src/fpr.rs")
negative=$(grep -F -c "$needle" "$out/negative/src/fpr.rs")
[[ $positive -eq $((negative+1)) ]] || exit 2
set +e
diff -u "$out/positive/src/fpr.rs" "$out/negative/src/fpr.rs" > "$out/actual-omitted-hook.diff"
diff_status=$?
set -e
[[ $diff_status == 1 ]] || exit 2
for arm in positive negative; do
 cargo generate-lockfile --offline --manifest-path "$out/$arm/Cargo.toml" > "$out/$arm-lock.txt" 2>&1
 (cd "$out/$arm" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$out/$arm-before.sha256"
 set +e
 timeout 120 cargo build --release --offline --locked --manifest-path "$out/$arm/Cargo.toml" > "$out/$arm-build.txt" 2>&1
 build_status=$?
 set -e
 printf '%s\n' "$build_status" > "$out/$arm-build.exit"
 [[ $build_status == 0 ]] || exit "$build_status"
 set +e
 (ulimit -v 2097152; timeout 120 "$CARGO_TARGET_DIR/release/n4-arithmetic-$arm-hook-control") > "$out/$arm-native.txt" 2>&1
 native_status=$?
 set -e
 printf '%s\n' "$native_status" > "$out/$arm-native.exit"
 expected=0; [[ $arm == positive ]] || expected=101
 [[ $native_status == "$expected" ]] || exit 1
 grep -F '"all_algebra_equal":true' "$out/$arm-native.txt" > /dev/null
 (cd "$out/$arm" && sha256sum --check "$out/$arm-before.sha256") > "$out/$arm-final-guards.txt"
done
grep -F '"observed_mul":11' "$out/positive-native.txt" > /dev/null
grep -F '"observed_mul":2' "$out/negative-native.txt" > /dev/null
(cd "$layout/original-layout" && sha256sum --check "$layout/original-785.sha256") > "$out/final-original-785.txt"
printf '0\n' > "$out/original.exit"
echo 'Positive native0; actual omitted coefficient-hook site native101 with SAME correct algebra, observed2 instead of11 products; original785 unchanged.'
