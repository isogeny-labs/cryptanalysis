#!/usr/bin/env python3
"""Check candidate ring-class sizes, 11 splitting, and selected prime."""
import json
from pathlib import Path
from sage.all import BinaryQF, ZZ, is_prime, kronecker, pari

P = Path(__file__).resolve().parent
cases = []
for dk in (-15, -39, -87, -183, -255):
    numbers = {str(f): int(pari.qfbclassno(ZZ(dk * f * f))) for f in (1, 2, 3, 6)}
    u = 0
    while True:
        value = u * u + 36 * (-dk)
        if value % 4 == 0 and is_prime(value // 4) and (value // 4) not in (2, 3, 5, 11):
            p = value // 4
            break
        u += 1
    cases.append({'DK': dk, 'kronecker_DK_11': int(kronecker(dk, 11)),
                  'ring_class_numbers': numbers, 'producer_prime': int(p),
                  'producer_trace_abs': u,
                  'norm2_order_at_f3': int(BinaryQF(2, 1, (1 - dk * 9) // 8).form_class().order())})
result = {'status': 'EXPLORATORY_MODULAR_GATE_SCAN', 'cases': cases}
(P / 'modular_gate_scan.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
