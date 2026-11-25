"""Checked-Sage order of the split norm-2 class at odd conductor 3."""
import json
from pathlib import Path
from sage.all import BinaryQF

HERE = Path(__file__).resolve().parent
form = BinaryQF(2, 1, 44)
assert int(form.discriminant()) == -351
order = int(form.form_class().order())
assert order == 12
result = {'status': 'verified', 'discriminant': -351,
          'norm2_form': [2, 1, 44], 'norm2_class_order': order}
(HERE / 'class_order_audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
