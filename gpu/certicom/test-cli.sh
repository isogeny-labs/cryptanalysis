#!/usr/bin/env bash
# Build only this task's release library/CLI and run the checked-in CLI tests.
# CERTICOM_TEST_BACKEND/WORKER select real hardware or explicit host emulation.
set -euo pipefail

certicom_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$certicom_root"
if [[ -f suite/Cargo.toml ]]; then
    certicom_manifest=suite/Cargo.toml
    certicom_crate=cryptanalysis_suite
    certicom_binary=ca-icx
    certicom_tests=suite/tests/certicom_solvers.rs
    certicom_bins=(--bin ca-icx --bin crax)
else
    certicom_manifest=Cargo.toml
    certicom_crate=crypto_lib
    certicom_binary=icx
    certicom_tests=tests/certicom_solvers.rs
    certicom_bins=(--bin icx)
fi
for certicom_tool in cargo rustc jq; do
    command -v "$certicom_tool" >/dev/null || {
        echo "Certicom CLI tests require $certicom_tool" >&2
        exit 2
    }
done
certicom_tmp=$(mktemp -d "${TMPDIR:-/tmp}/certicom-cli.XXXXXXXX")
trap 'rm -rf -- "$certicom_tmp"' EXIT

# Cargo integration-test builds also select unrelated binaries in these host
# crates. Use Cargo's actual release artifacts, not guessed dependency hashes.
cargo build --manifest-path "$certicom_manifest" --release --lib \
    "${certicom_bins[@]}" --message-format=json > "$certicom_tmp/artifacts.jsonl"
certicom_externs=()
certicom_dependency_dir=
for certicom_dep in "$certicom_crate" num_bigint num_traits serde_json; do
    certicom_rlib=$(jq -rs --arg name "$certicom_dep" '
        [.[] | select(.reason == "compiler-artifact" and .target.name == $name)
         | select($name != "num_bigint" or (.package_id | test("num-bigint(@| )0\\.4\\.")))
         | .filenames[] | select(endswith(".rlib"))] | unique
         | if length == 1 then .[0] else error("expected one release artifact for " + $name) end
    ' "$certicom_tmp/artifacts.jsonl")
    certicom_externs+=(--extern "$certicom_dep=$certicom_rlib")
    if [[ "$certicom_dep" == num_traits ]]; then
        certicom_dependency_dir=$(dirname -- "$certicom_rlib")
    fi
done
certicom_executable=$(jq -rs --arg name "$certicom_binary" '
    [.[] | select(.reason == "compiler-artifact" and .target.name == $name)
     | .executable | select(. != null)] | unique
     | if length == 1 then .[0] else error("expected one release CLI executable") end
' "$certicom_tmp/artifacts.jsonl")
certicom_test_entry() {
    local certicom_program=$1 certicom_label=$2
    shift 2
    env "CARGO_BIN_EXE_$certicom_binary=$certicom_program" \
        rustc --edition=2021 --test "$certicom_tests" \
        -L "dependency=$certicom_dependency_dir" "${certicom_externs[@]}" \
        -o "$certicom_tmp/$certicom_label-tests"
    "$certicom_tmp/$certicom_label-tests" --test-threads=1 --nocapture "$@"
}
certicom_test_entry "$certicom_executable" "$certicom_binary" "$@"
if [[ "$certicom_binary" == ca-icx ]]; then
    CERTICOM_CRAX_EXECUTABLE=$(jq -rs '
        [.[] | select(.reason == "compiler-artifact" and .target.name == "crax")
         | .executable | select(. != null)] | unique
         | if length == 1 then .[0] else error("expected one release crax executable") end
    ' "$certicom_tmp/artifacts.jsonl")
    export CERTICOM_CRAX_EXECUTABLE
    # Thin routing shim: every test still executes the actual release crax.
    cat > "$certicom_tmp/crax-icx" <<'SH'
#!/usr/bin/env bash
exec "$CERTICOM_CRAX_EXECUTABLE" icx "$@"
SH
    chmod +x "$certicom_tmp/crax-icx"
    certicom_test_entry "$certicom_tmp/crax-icx" crax "$@"
fi
