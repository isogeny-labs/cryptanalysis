"""Independent full Sage census of the fixed W29 first-mask prefix."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'prefix_audit_protocol.json').read_text())
assert cfg['status'] == 'FROZEN_BEFORE_SAGE_CENSUS'
for name, item in cfg['sources'].items():
    assert sha(item['path']) == item['sha256'], name
native = json.loads(Path(cfg['sources']['prefix_result']['path']).read_text())['native']
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
seed = 898618
prefix = 3
count = 0
left_count = 0
right_count = 0
checked = 0
first = None
last = None
start = time.monotonic()
status = 'COMPLETE_INDEPENDENT_SAGE_PREFIX_CENSUS'
for low in range(1 << 11):
    for high in range(1 << 9):
        a = prefix | (low << 8) | (high << 20)
        b = a ^ seed
        assert a < b < (1 << 29) and a & 255 == prefix and not a & (1 << 19)
        wa, wb = F.from_integer(a << 1), F.from_integer(b << 1)
        assert wa.trace() == 0 and wb.trace() == 0
        va = (1 / wa).trace() == 0
        vb = (1 / wb).trace() == 0
        left_count += va
        right_count += vb
        if va and vb:
            count += 1
            first = a if first is None else min(first, a)
            last = a if last is None else max(last, a)
        checked += 1
        if checked % 4096 == 0:
            if time.monotonic() - start >= cfg['wall_cap_seconds']:
                status = 'WALL_CAP_PARTIAL_CENSUS'
                break
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= cfg['rss_cap_bytes']:
                status = 'RSS_CAP_PARTIAL_CENSUS'
                break
    if status != 'COMPLETE_INDEPENDENT_SAGE_PREFIX_CENSUS':
        break
result = {'status':status,'canonical_masks_checked':checked,
          'eligible_edges':count,'left_inverse_trace_zero':left_count,
          'right_inverse_trace_zero':right_count,
          'first_eligible':first,'last_eligible':last,
          'wall_seconds':time.monotonic()-start,
          'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'audit_protocol_sha256':sha(HERE/'prefix_audit_protocol.json'),
          'auditor_sha256':sha(Path(__file__))}
if status == 'COMPLETE_INDEPENDENT_SAGE_PREFIX_CENSUS':
    assert checked == 1 << 20
    assert count == native['eligible_edges']
    assert left_count == native['left_inverse_trace_zero']
    assert right_count == native['right_inverse_trace_zero']
    assert first == native['first_eligible'] and last == native['last_eligible']
(HERE/'prefix_audit_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True),flush=True)
