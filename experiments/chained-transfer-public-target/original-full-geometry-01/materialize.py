"""Literal nominal-type derivatives only; research arithmetic is Rust/Lean."""
from pathlib import Path
import hashlib
import json

p = Path(__file__).resolve().parent
s = p.parent
g = p / 'generated'
g.mkdir()
rows = []
for source, destination, patches in [
    ('odd-product-maps/src/adapter.rs', 'adapter.rs', [
        ('chained_n4_odd_product_models', 'chained_n4_paired_fourth_preflight::models', 3),
    ]),
    ('odd-product-maps/src/norm.rs', 'norm.rs', []),
    ('beta-complete-evaluator/src/lib.rs', 'quadratic.rs', [
        ('use chained_n4_odd_product_maps::Adapter;', 'use crate::Adapter;', 1),
        ('pub mod complete;\n', '', 1),
        ('\n#[cfg(test)]\nmod tests;\n\n#[cfg(test)]\nmod complete_tests;\n\n#[cfg(test)]\nmod exceptional_tests;\n', '\n', 1),
    ]),
]:
    original = (s / source).read_bytes()
    body = original
    for old, new, count in patches:
        assert body.count(old.encode()) == count, (source, old)
        body = body.replace(old.encode(), new.encode())
    (g / destination).write_bytes(body)
    rows.append(dict(source=source, whole_source_sha256=hashlib.sha256(original).hexdigest(),
                     explicit_nominal_or_module_patches=patches, generated=destination,
                     generated_sha256=hashlib.sha256(body).hexdigest()))
(g / 'custody.json').write_text(json.dumps(dict(
    protocol='ORIGINAL_FULL_GROUP_CHAIN_PROTOCOL_01, claim1539b6, publishedd4f9d6b before code',
    literal_sources=rows,
    scope='No mathematical formula changed. Old variant retained; old tests and complete wrapper remain in their original crate.'
), indent=2) + '\n')
print('Three literal geometry modules assembled with explicit nominal/module rewrites')
