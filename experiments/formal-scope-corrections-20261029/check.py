#!/usr/bin/env python3
"""Exact arithmetic behind the 2026-10-29 formal-scope corrections (no external inputs)."""
import json, sys
out = {
    "cubic_gluing_determinant": {
        "det_diag_3_4_over_Z": 3 * 4,
        "q_cubed": 3 ** 3,
        "equal_over_Z": 3 * 4 == 3 ** 3,
        "equal_mod_5": (3 * 4) % 5 == (3 ** 3) % 5,
        "residues_mod_5": [(3 * 4) % 5, (3 ** 3) % 5],
    },
}
json.dump(out, sys.stdout, indent=1)
print()
assert not out["cubic_gluing_determinant"]["equal_over_Z"]
assert out["cubic_gluing_determinant"]["equal_mod_5"]
