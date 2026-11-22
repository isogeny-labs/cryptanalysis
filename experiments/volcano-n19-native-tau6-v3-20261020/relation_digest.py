"""Relation digests and strict JSON for protocol v3, in plain Python (never preparsed).

Why this module exists. In v2 `relation_digests` lived in arm.sage. The Sage
preparser rewrites every integer literal of a .sage file as a Sage
`Integer`, so its line

    row[col] = (row.get(col, 0) + sg * pow(int(lam), int(e), int(p))) % int(p)

ran as `row.get(col, Integer(0))`. Integer + int and Integer % int are Sage
Integers, every value of `rows` was one, and `json.dumps(rows)` raised
`TypeError: Object of type Integer is not JSON serializable` in every timed
IC row of run 39376405326 (B, N, Naa and NX on all 16 points). The two
digests before it (`ordered`, `canonical`) were built with `int()` and
passed. See diagnosis/README.md.

v3 moves the digest here, where no preparser runs, converts every input with
`operator.index` (exact; refuses floats and non-integral objects), and builds
every value from Python ints. arm.sage, the verifier and the local checks
import this one module, so the verifier recomputes each digest from the raw
relations a row records.

`plain` is the strict converter for everything a row writes: Python
primitives pass; anything with `__index__` (Sage Integer, int-valued ring
elements) becomes an exact int; Sage real numbers become floats; any other
object raises TypeError naming its path, instead of v2's `jplain`, which fell
back to `str()` silently.
"""
import hashlib
import json
import operator

REAL_TYPE_NAMES = ('RealNumber', 'RealDoubleElement', 'RealLiteral', 'float64')


def _int(x):
    if isinstance(x, bool):
        raise TypeError('bool where an integer was expected')
    return operator.index(x)


def canonical_relation(rel):
    """One decomposition as a list of [column, sign, Frobenius power] Python ints."""
    out = [[_int(c), _int(s), _int(e)] for c, s, e in rel]
    for c, s, e in out:
        if s not in (1, -1) or c < 0 or e < 0:
            raise ValueError('malformed relation term %r' % ([c, s, e],))
    return out


def sha256_json(obj):
    """SHA-256 of compact JSON with sorted keys (no default: an unexpected type is an
    error, never coerced). For the relation digests (lists of ints only) this is
    byte for byte v2's definition."""
    return hashlib.sha256(json.dumps(obj, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


def relation_digests(rels, lam, p):
    """ordered: the decompositions as returned; canonical: each one as a sorted multiset
    of (column, sign, Frobenius power); rows: the matrix rows tauDlp builds from them
    (column -> sum sign * lambda^e mod p), as sorted [column, value] pairs.
    The definitions are v2's; only the types are made explicit."""
    lam, p = _int(lam), _int(p)
    ordered = [canonical_relation(r) for r in rels]
    canon = [sorted(r) for r in ordered]
    rows = []
    for r in ordered:
        row = {}
        for col, sg, e in r:
            row[col] = (row.get(col, int(0)) + sg * pow(lam, e, p)) % p
        rows.append([[c, v] for c, v in sorted(row.items())])
    for row in rows:
        for c, v in row:
            if type(c) is not int or type(v) is not int:
                raise TypeError('relation row holds a non-int')
    return {'ordered_sha256': sha256_json(ordered), 'canonical_sha256': sha256_json(canon),
            'rows_sha256': sha256_json(rows), 'count': len(ordered)}


def plain(o, path='$'):
    """Strict conversion to JSON types; raises TypeError on anything unexpected."""
    if o is None or isinstance(o, (bool, str)):
        return o
    if type(o) is int:
        return o
    if type(o) is float:
        return o
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if isinstance(k, str):
                key = k
            elif hasattr(k, '__index__') and not isinstance(k, bool):
                key = str(_int(k))
            else:
                raise TypeError('%s: dict key of type %s' % (path, type(k).__name__))
            if key in out:
                raise TypeError('%s: duplicate key %s after conversion' % (path, key))
            out[key] = plain(v, '%s.%s' % (path, key))
        return out
    if isinstance(o, (list, tuple)):
        return [plain(v, '%s[%d]' % (path, i)) for i, v in enumerate(o)]
    if isinstance(o, int):           # int subclasses (not bool, handled above)
        return int(o)
    if hasattr(o, '__index__'):
        try:
            return operator.index(o)
        except Exception as e:
            raise TypeError('%s: object of type %s has no exact integer value (%s)' % (path, type(o).__name__, e))
    if isinstance(o, float) or type(o).__name__ in REAL_TYPE_NAMES:
        return float(o)
    raise TypeError('%s: object of type %s is not a JSON value (convert it explicitly)' %
                    (path, type(o).__name__))


def dumps(o, **kw):
    """json.dumps of plain(o); no default= hook, so nothing is converted silently."""
    return json.dumps(plain(o), **kw)
