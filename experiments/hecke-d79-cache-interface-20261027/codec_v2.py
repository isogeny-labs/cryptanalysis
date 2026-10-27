"""Explicitly validated v2 decoder for canonical degree-13 Hecke function JSON."""
import hashlib
import json
import math
from pathlib import Path

from sage.all import QQ

SCHEMA = 'hecke13-functions-v1'
EXPECTED_KEYS = ({(13, 'x', k) for k in range(1, 15)} |
                 {(13, 'xy', k) for k in range(14)})


class CacheValidationError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(condition, code):
    if not condition:
        raise CacheValidationError(code)


def canonical_bytes(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False) + '\n').encode('utf-8')


def rat(value):
    q = QQ(value)
    n, d = int(q.numerator()), int(q.denominator())
    require(d > 0 and math.gcd(abs(n), d) == 1, 'RATIONAL_NONCANONICAL')
    return [n, d]


def checked_rat(value):
    require(type(value) is list and len(value) == 2, 'RATIONAL_SHAPE')
    n, d = value
    require(type(n) is int and type(d) is int and d > 0, 'RATIONAL_SHAPE')
    require(math.gcd(abs(n), d) == 1, 'RATIONAL_NONCANONICAL')
    return QQ(n) / QQ(d)


def terms_from_dict(coeffs):
    require(type(coeffs) is dict, 'TERMS_SHAPE')
    terms = []
    for key, coeff in sorted(coeffs.items()):
        require(type(key) is tuple and len(key) == 2, 'MONOMIAL_SHAPE')
        a, b = key
        require(type(a) is int and type(b) is int and a >= 0 and b in (0, 1),
                'MONOMIAL_SHAPE')
        require(QQ(coeff) != 0, 'ZERO_COEFFICIENT')
        terms.append([a, b, rat(coeff)])
    return terms


def dict_from_terms(terms):
    require(type(terms) is list, 'TERMS_SHAPE')
    out = {}
    last = None
    for term in terms:
        require(type(term) is list and len(term) == 3, 'TERM_SHAPE')
        a, b, coefficient = term
        require(type(a) is int and type(b) is int and a >= 0 and b in (0, 1),
                'MONOMIAL_SHAPE')
        require(last is None or (a, b) > last, 'TERM_ORDER_OR_DUPLICATE')
        last = (a, b)
        value = checked_rat(coefficient)
        require(value != 0, 'ZERO_COEFFICIENT')
        out[a, b] = value
    return out


def payload_from_build(funcs, jfun, source_sha256):
    require(type(funcs) is dict and set(funcs) == EXPECTED_KEYS, 'FUNCTION_SET')
    entries = []
    for key, terms in sorted(funcs.items()):
        entries.append({'key': list(key), 'terms': terms_from_dict(terms)})
    require(type(jfun) is tuple and len(jfun) == 3, 'J_FUNCTION_SHAPE')
    A, x0, cusp = jfun
    require(not cusp.is_zero(), 'CUSP_INVALID')
    return {'schema': SCHEMA, 'source_sha256': source_sha256,
            'degrees': [13], 'funcs': entries,
            'jfun': {'A_terms': terms_from_dict(A), 'x0': rat(x0),
                     'cusp': [rat(cusp[0]), rat(cusp[1])]}}


def build_from_payload(payload, H, source_sha256):
    require(type(payload) is dict and set(payload) ==
            {'schema', 'source_sha256', 'degrees', 'funcs', 'jfun'}, 'PAYLOAD_SHAPE')
    require(payload['schema'] == SCHEMA, 'SCHEMA_MISMATCH')
    require(payload['source_sha256'] == source_sha256, 'SOURCE_MISMATCH')
    require(payload['degrees'] == [13], 'DEGREE_MISMATCH')
    entries = payload['funcs']
    require(type(entries) is list and len(entries) == 28, 'FUNCTION_COUNT')
    funcs = {}
    last = None
    for item in entries:
        require(type(item) is dict and set(item) == {'key', 'terms'}, 'FUNCTION_SHAPE')
        key = item['key']
        require(type(key) is list and len(key) == 3, 'FUNCTION_KEY_SHAPE')
        ell, kind, k = key
        require(type(ell) is int and type(kind) is str and type(k) is int,
                'FUNCTION_KEY_SHAPE')
        key_tuple = (ell, kind, k)
        require(key_tuple in EXPECTED_KEYS, 'FUNCTION_KEY_INVALID')
        require(last is None or key_tuple > last, 'FUNCTION_ORDER_OR_DUPLICATE')
        last = key_tuple
        funcs[key_tuple] = dict_from_terms(item['terms'])
    require(set(funcs) == EXPECTED_KEYS, 'FUNCTION_SET')
    j = payload['jfun']
    require(type(j) is dict and set(j) == {'A_terms', 'x0', 'cusp'},
            'J_FUNCTION_SHAPE')
    A = dict_from_terms(j['A_terms'])
    x0 = checked_rat(j['x0'])
    coords = j['cusp']
    require(type(coords) is list and len(coords) == 2, 'CUSP_SHAPE')
    try:
        cusp = H.E0(checked_rat(coords[0]), checked_rat(coords[1]))
    except Exception as exc:
        raise CacheValidationError('CUSP_INVALID') from exc
    require(not cusp.is_zero() and cusp[0] == x0, 'CUSP_INVALID')
    return funcs, (A, x0, cusp)


def artifact_bytes(funcs, jfun, source_sha256):
    return canonical_bytes(payload_from_build(funcs, jfun, source_sha256))


def load_artifact(path, expected_sha256, H, source_sha256):
    path = Path(path)
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise CacheValidationError('CACHE_MISSING') from exc
    actual = hashlib.sha256(raw).hexdigest()
    require(actual == expected_sha256, 'ARTIFACT_DIGEST_MISMATCH')
    require(path.name == f'hecke13-{actual}.json', 'ARTIFACT_FILENAME_MISMATCH')
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CacheValidationError('ARTIFACT_JSON_INVALID') from exc
    require(raw == canonical_bytes(obj), 'ARTIFACT_NONCANONICAL_JSON')
    funcs, jfun = build_from_payload(obj, H, source_sha256)
    require(artifact_bytes(funcs, jfun, source_sha256) == raw,
            'ARTIFACT_ROUNDTRIP_MISMATCH')
    return funcs, jfun, len(raw)
