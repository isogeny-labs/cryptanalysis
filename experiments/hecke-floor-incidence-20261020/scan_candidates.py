#!/usr/bin/env python3
"""Enumerate small ramified-3, split-2 discriminants for a held-out class walk."""
import json
from pathlib import Path

from sage.all import BinaryQF, QuadraticField

P = Path(__file__).resolve().parent
cases = []
for dk in range(-15, -350, -24):
    if int(QuadraticField(dk).discriminant()) != dk:
        continue
    disc3 = dk * 9
    form = BinaryQF(2, 1, (1 - disc3) // 8)
    order = int(form.form_class().order())
    cases.append({'DK': dk, 'f': 6, 'odd_conductor': 3,
                  'norm2_order': order, 'blocks_per_cycle': order // 6 if order % 6 == 0 else None,
                  'norm2_form': [2, 1, (1 - disc3) // 8]})
result = {'status': 'EXPLORATORY_CLASS_ORDER_SCAN', 'cases': cases}
(P / 'scan_candidates.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
