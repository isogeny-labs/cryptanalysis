"""Copy literal Rust helpers at exact declared boundaries; no arithmetic."""
from pathlib import Path
import hashlib
import json

p = Path(__file__).resolve().parent
s = p.parent
g = p / 'generated'
g.mkdir()
rows = []

def section(source, start, end, destination):
    whole = (s / source).read_bytes()
    a, b = start.encode(), end.encode()
    assert whole.count(a) == 1 and whole.count(b) == 1
    body = whole[whole.index(a):whole.index(b)]
    (g / destination).write_bytes(body)
    rows.append(dict(source=source, source_sha256=hashlib.sha256(whole).hexdigest(),
                     start=start, end_before=end, destination=destination,
                     literal_sha256=hashlib.sha256(body).hexdigest(), explicit_body_changes=[]))

section('odd-source/src/lib.rs', 'fn er(', 'fn digest(', 'encoding.rs')
section('odd-source/src/lib.rs', 'fn cubic(', 'fn identity_residual(', 'polynomial.rs')
section('odd-source/src/lib.rs', 'fn homogeneous(', 'fn multiplication_13(', 'rational.rs')
section('nondual13-preflight/src/append.rs', 'fn rational_curve_residual(', 'pub struct SecondHop', 'curve_residual.rs')
section('norm-halving-evaluator/src/direct.rs', 'pub fn halving_quartic(', 'fn adapters(', 'halving.rs')
section('norm-halving-evaluator/src/lib.rs', 'fn parse_packet(', '#[derive(Clone, Copy)]', 'parse_packet.rs')
body = (s / 'norm-halving-evaluator/src/literal_halves.rs').read_bytes()
(g / 'literal_halves.rs').write_bytes(body)
rows.append(dict(source='norm-halving-evaluator/src/literal_halves.rs', whole_literal_sha256=hashlib.sha256(body).hexdigest(), destination='literal_halves.rs', explicit_body_changes=[]))
section('twisted-pair-preflight/src/twist_append.rs', 'fn eval_rational(', 'fn compare_degree13_recipe(', 'eval_rational.rs')
(g / 'custody.json').write_text(json.dumps(dict(protocol='1539b6 publishedd4f9d6b before code', literal_sections=rows, scope='Only module placement and imports change; all selected bodies remain exact original bytes.'), indent=2) + '\n')
print('Seven literal helper sections copied; no mathematical body change')
