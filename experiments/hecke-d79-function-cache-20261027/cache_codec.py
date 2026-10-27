"""Canonical JSON codec for one rational degree-13 Hecke function build."""
import hashlib
import json
import math
from pathlib import Path

from sage.all import QQ

SCHEMA = 'hecke13-functions-v1'


def canonical_bytes(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode('utf-8')


def rat(value):
    q = QQ(value)
    n, d = int(q.numerator()), int(q.denominator())
    assert d > 0 and math.gcd(abs(n), d) == 1
    return [n, d]


def checked_rat(value):
    assert isinstance(value, list) and len(value) == 2
    n, d = value
    assert type(n) is int and type(d) is int and d > 0
    assert math.gcd(abs(n), d) == 1
    return QQ(n) / QQ(d)


def terms_from_dict(coeffs):
    terms = []
    for (a, b), coeff in sorted(coeffs.items()):
        assert type(a) is int and type(b) is int and a >= 0 and b in (0, 1)
        assert QQ(coeff) != 0
        terms.append([a, b, rat(coeff)])
    return terms


def dict_from_terms(terms):
    assert isinstance(terms, list)
    out = {}
    last = None
    for term in terms:
        assert isinstance(term, list) and len(term) == 3
        a, b, c = term
        assert type(a) is int and type(b) is int and a >= 0 and b in (0, 1)
        assert last is None or (a, b) > last
        last = (a, b)
        value = checked_rat(c)
        assert value != 0
        out[a, b] = value
    return out


def payload_from_build(funcs, jfun, source_sha256):
    assert isinstance(funcs, dict) and len(funcs) == 28
    entries = []
    for (ell, kind, k), terms in sorted(funcs.items()):
        assert ell == 13 and kind in ('x', 'xy')
        assert (kind == 'x' and 1 <= k <= 14) or (kind == 'xy' and 0 <= k <= 13)
        entries.append({'key': [ell, kind, k], 'terms': terms_from_dict(terms)})
    assert {tuple(x['key']) for x in entries} == (
        {(13, 'x', k) for k in range(1, 15)} |
        {(13, 'xy', k) for k in range(14)})
    A, x0, cusp = jfun
    assert not cusp.is_zero()
    payload = {'schema': SCHEMA, 'source_sha256': source_sha256,
               'degrees': [13], 'funcs': entries,
               'jfun': {'A_terms': terms_from_dict(A), 'x0': rat(x0),
                        'cusp': [rat(cusp[0]), rat(cusp[1])]}}
    return payload


def build_from_payload(payload, H, source_sha256):
    assert type(payload) is dict and set(payload) == {
        'schema', 'source_sha256', 'degrees', 'funcs', 'jfun'}
    assert payload['schema'] == SCHEMA
    assert payload['source_sha256'] == source_sha256
    assert payload['degrees'] == [13]
    entries = payload['funcs']
    assert isinstance(entries, list) and len(entries) == 28
    funcs = {}
    last = None
    for item in entries:
        assert type(item) is dict and set(item) == {'key', 'terms'}
        key = item['key']
        assert isinstance(key, list) and len(key) == 3
        ell, kind, k = key
        assert type(ell) is int and type(kind) is str and type(k) is int
        assert ell == 13 and kind in ('x', 'xy')
        assert (kind == 'x' and 1 <= k <= 14) or (kind == 'xy' and 0 <= k <= 13)
        assert last is None or tuple(key) > last
        last = tuple(key)
        funcs[tuple(key)] = dict_from_terms(item['terms'])
    assert set(funcs) == ({(13, 'x', k) for k in range(1, 15)} |
                          {(13, 'xy', k) for k in range(14)})
    j = payload['jfun']
    assert type(j) is dict and set(j) == {'A_terms', 'x0', 'cusp'}
    A = dict_from_terms(j['A_terms'])
    x0 = checked_rat(j['x0'])
    coords = j['cusp']
    assert isinstance(coords, list) and len(coords) == 2
    cusp = H.E0(checked_rat(coords[0]), checked_rat(coords[1]))
    assert not cusp.is_zero() and cusp[0] == x0
    return funcs, (A, x0, cusp)


def artifact_bytes(funcs, jfun, source_sha256):
    return canonical_bytes(payload_from_build(funcs, jfun, source_sha256))


def load_artifact(path, expected_sha256, H, source_sha256):
    path = Path(path)
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ValueError('ARTIFACT_DIGEST_MISMATCH')
    if path.name != f'hecke13-{actual}.json':
        raise ValueError('ARTIFACT_FILENAME_MISMATCH')
    obj = json.loads(raw)
    if raw != canonical_bytes(obj):
        raise ValueError('ARTIFACT_NONCANONICAL_JSON')
    funcs, jfun = build_from_payload(obj, H, source_sha256)
    if artifact_bytes(funcs, jfun, source_sha256) != raw:
        raise ValueError('ARTIFACT_ROUNDTRIP_MISMATCH')
    return funcs, jfun, len(raw)
