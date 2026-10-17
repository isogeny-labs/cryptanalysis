"""Select the first new valid N131 W23 first-slot code after mask 46."""
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

D = Path(__file__).resolve().parent
ROOT = D.parent
ARCH = ROOT / 'n41_n131_rr_code_family_span_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((D / 'holdout_prepare_protocol.json').read_text())
assert protocol['producer_sha256'] == sha(Path(__file__))
assert all(sha(Path(path)) == digest for path, digest in protocol['sources'].items())
panel = json.loads((ARCH / 'panel_n131_v2.json').read_text())
R = PolynomialRing(GF(2), 't')
t = R.gen()
F = GF(2**131, name='t', modulus=t**131+t**13+t**2+t+1)
E = EllipticCurve(F, [1,0,0,0,1])


def dec(word):
    return F(R([(int(word)>>i)&1 for i in range(131)]))


def enc(value):
    return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))


def halftrace(value):
    total = F.zero()
    term = value
    for _ in range(66):
        total += term
        term = term**4
    assert total**2+total == value
    return total


def source(mask):
    w = dec(mask << 1)
    assert w and w.trace() == 0 and (1/w).trace() == 0
    x = 1+1/halftrace(w)
    points = E.lift_x(x, all=True)
    assert len(points) == 2
    return points[0]


def key(mask):
    point = 4*source(mask)
    assert point != E(0)
    x = point[0]
    least = None
    for _ in range(131):
        word = enc(x)
        least = word if least is None or word < least else least
        x = x**2
    return least


def roots(a,b):
    left,right = source(a),source(b)
    groups = {}
    for p in (left,-left):
        for q in (right,-right):
            z = p+q
            assert z != E(0)
            row = [enc(z[0]),enc(z[1])]
            groups.setdefault(row[0],set()).add(tuple(row))
    assert len(groups)==2 and all(len(rows)==2 for rows in groups.values())
    return [[list(row) for row in sorted(groups[x])] for x in sorted(groups)]


fixed = panel['variants'] + []
fixed_masks = {mask for row in fixed for mask in row['masks']}
fixed_masks.update(mask for row in panel.get('fixed_edges', []) for mask in row['masks'])
prior = json.loads((ROOT / 'n41_n131_sixpair_rr_root_span_20261016' / 'frozen_panels.json').read_text())['n131']
suffix_masks = {mask for row in prior['edges'][1:] for mask in row['masks']}
excluded_keys = {key(mask) for mask in suffix_masks}
excluded_keys.update(key(mask) for mask in fixed_masks)
tested = 0
for mask in range(47,256):
    mate = mask ^ 898618
    tested += 1
    if mask in suffix_masks or mate in suffix_masks or mask in fixed_masks or mate in fixed_masks:
        continue
    w,z = dec(mask<<1),dec(mate<<1)
    if not w or not z or w.trace()!=0 or z.trace()!=0:
        continue
    if (1/w).trace()!=0 or (1/z).trace()!=0:
        continue
    keys = [key(mask),key(mate)]
    if keys[0]==keys[1] or any(item in excluded_keys for item in keys):
        continue
    root_rows = roots(mask,mate)
    break
else:
    raise RuntimeError('NO_VALID_HOLDOUT_MASK_IN_DECLARED_RANGE')
result = {'status':'FROZEN_PROSPECTIVE_N131_SOURCE_HOLDOUT',
          'protocol_sha256':sha(D/'holdout_prepare_protocol.json'),
          'first_mask':mask,'mate_mask':mate,'orbit_keys':keys,
          'roots':root_rows,'masks_tested':tested,
          'target':panel['target'],'fixed_points':panel['fixed_points'],
          'field_degree':131,'field_modulus':panel['field_modulus']}
(D/'holdout_source.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'first_mask':mask,
                  'mate_mask':mate,'masks_tested':tested}))
