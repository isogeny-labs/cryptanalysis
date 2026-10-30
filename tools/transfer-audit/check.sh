#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
audit_root="tools/transfer-audit"
audit_out="${1:-$(mktemp -d "${TMPDIR:-/tmp}/transfer-audit-check.XXXXXX")}"
mkdir -p "$audit_out"
audit_out="$(cd "$audit_out" && pwd)"
if [ -e "$audit_out/completed.json" ] || [ -e "$audit_out/b163-certificate.json" ]; then
  echo "refusing to overwrite a completed or partial fixture replay" >&2
  exit 2
fi
cargo fmt --manifest-path "$audit_root/Cargo.toml" -- --check
cargo clippy --release --locked --manifest-path "$audit_root/Cargo.toml" --all-targets -- -D warnings
cargo test --release --locked --manifest-path "$audit_root/Cargo.toml"
cargo build --release --locked --manifest-path "$audit_root/Cargo.toml"
"$audit_root/target/release/transfer-audit" audit --input "$audit_root/fixtures/b163.json" --output "$audit_out/b163-certificate.json"
"$audit_root/target/release/transfer-audit" verify --certificate "$audit_out/b163-certificate.json"
# Fixed-fixture correctness replay only. Research sweeps require checkpoint.sh gate.
lean --version | tee "$audit_out/lean-version.txt"
python3 -c 'import pathlib,sys; assert "version 4.34.1," in pathlib.Path(sys.argv[1]).read_text(), "unexpected Lean version"' "$audit_out/lean-version.txt"
lean -o "$audit_out/TransferAudit.olean" tools/lean/transfer-audit/TransferAudit.lean > "$audit_out/lean-build.txt" 2>&1
LEAN_PATH="$audit_out" lean --run tools/lean/AuditAxioms.lean TransferAudit > "$audit_out/lean-audit.txt" 2>&1
python3 - "$audit_out" <<'PY'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
text = (p / 'lean-audit.txt').read_text()
expected = {'b163_genus63_bound', 'b163_genus64_bound', 'b163_obstruction',
            'closed_coverage', 'divisibility_obstruction', 'integerWeilBound.eq_1',
            'invariant_transport', 'pair63', 'pair64', 'size_obstruction',
            'sqrt_lower', 'sqrt_upper'}
actual = {line.split()[1].removeprefix('TransferAudit.')
          for line in text.splitlines() if line.startswith('ok    ')}
assert actual == expected, (actual, expected)
assert text.rstrip().endswith('audited 12 theorems in [TransferAudit]; 0 failing, 0 trusted (native_decide)')
c = json.loads((p / 'b163-certificate.json').read_text())
assert c['source']['generator_exact_order_verified']
assert c['same_field_genus_three']['source_generator_image_order_verified']
assert c['subfields'][0]['excluded_genus_interval_inclusive'] == [0,63]
assert c['all_possible_transfers_ruled_out'] is False
(p / 'completed.json').write_text(json.dumps({'scope':'fixed-fixture correctness, not a research sweep or speed measurement',
    'lean_transitively_audited_theorems':12,'input_sha256':c['input_sha256'],
    'implementation_sha256':c['implementation_sha256']}, indent=2)+'\n')
PY
echo "fixed-fixture checks passed: $audit_out"
