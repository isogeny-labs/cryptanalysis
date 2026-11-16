#!/usr/bin/env python3
"""CT142 receipt guard for original q223 CT141 native timing. [pcc:unverified]

No native execution, budget admission, or complete-ECDLP performance claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import statistics as st
import tempfile
from fractions import Fraction
from pathlib import Path
import check_pair  # Unmodified CT126 schema and synthetic fixture, SHA-pinned by CT141.

ARMS = check_pair.ARMS
SEQUENCE = check_pair.SEQUENCE
LABELS = check_pair.LABELS
SUFFIX = ('.json', '.stderr', '.resources.txt', '.exit-status.txt')
EXPECTED_OUTPUTS = {a + s for a in ARMS for s in SUFFIX}
MAX_RSS = 2097152  # 2 GiB in KiB


def require(ok, description):
    if not ok:
        raise ValueError('CT142 REJECTED: ' + description)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1 << 20), b''):
            h.update(part)
    return h.hexdigest()


def hashes(out, name, expected_count, expected=None):
    """Validate live bytes and absolute source/binary and output receipts."""
    lines = (out / name).read_text().splitlines()
    require(len(lines) == expected_count, name + ' wrong hash roster')
    found = {}
    for row in lines:
        require(len(row) > 66 and row[64:66] == '  ' and
                re.fullmatch('[0-9a-f]{64}', row[:64]), name + ' malformed hash')
        path = Path(row[66:])
        require(path.is_absolute() and path.is_file() and not path.is_symlink(),
                name + ' path missing/symlink')
        key = path.name if name == 'outputs-sha256.txt' else str(path)
        require(key not in found, name + ' duplicate file')
        if name == 'outputs-sha256.txt':
            require(path.parent.resolve() == out.resolve(), name + ' escaped output path')
        require(sha(path) == row[:64], name + ' SHA mismatch ' + path.name)
        found[key] = row[:64]
    if expected is not None:
        got = set(found) if name == 'outputs-sha256.txt' else {Path(k).name for k in found}
        require(got == expected, name + ' file roster mismatch')
    return found


def gnu_resources(path):
    data = path.read_text()
    def one(pattern, key):
        vals = re.findall(pattern, data, flags=re.M)
        require(len(vals) == 1, path.name + ' missing/duplicate ' + key)
        return vals[0]
    w = one(r'^\s*Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*(\S+)\s*$', 'elapsed')
    bits = w.split(':')
    require(len(bits) in (2, 3), 'invalid elapsed format')
    try:
        seconds = 0.0
        for x in bits:
            seconds = seconds * 60 + float(x)
    except ValueError as e:
        raise ValueError('nonnumeric GNU elapsed') from e
    require(seconds > 0, 'nonpositive GNU elapsed')
    rss = int(one(r'^\s*Maximum resident set size \(kbytes\):\s*(\d+)\s*$', 'RSS'))
    require(0 < rss <= MAX_RSS, 'zero/over-limit GNU RSS')
    status = int(one(r'^\s*Exit status:\s*(\d+)\s*$', 'status'))
    require(status == 0, 'GNU process nonzero exit')
    return {'elapsed_seconds': seconds, 'peak_rss_kib': rss}


def per_call(rec, label):
    r = rec['timed'][label]
    return [Fraction(x, r['repetitions_per_block']) for x in r['raw_block_ns']]


def inspect(out):
    require((out / 'sequence.txt').read_text().splitlines() == list(SEQUENCE),
            'wrong process ABBA order')
    host = (out / 'host.txt').read_text()
    require('rustc' in host and 'cargo' in host, 'missing host receipt')
    outputs = hashes(out, 'outputs-sha256.txt', 16, EXPECTED_OUTPUTS)
    source = hashes(out, 'source-sha256.txt', 6)
    binary = hashes(out, 'binary-sha256.txt', 2, {'ct126-price', 'ct126-price-reuse'})
    require(any(Path(k).name == 'main.rs' for k in source) and
            any(Path(k).name == 'check_pair.py' for k in source), 'missing pinned sources')
    data, resources = {}, {}
    for arm in ARMS:
        require((out / (arm + '.exit-status.txt')).read_text().strip() == '0',
                arm + ' native status nonzero')
        resources[arm] = gnu_resources(out / (arm + '.resources.txt'))
        data[arm] = json.loads((out / (arm + '.json')).read_text())
    canonical = check_pair.audit(data)  # Also checks all 4 original public identities.
    aa, paired, all_deltas = {}, {}, []
    for label in LABELS + ('setup_construct_ns',):
        def cost(arm):
            return (Fraction(data[arm][label]) if label == 'setup_construct_ns'
                    else st.median(per_call(data[arm], label)))
        v1 = cost('original-1') / cost('original-2')
        v2 = cost('reuse-1') / cost('reuse-2')
        require(all(Fraction(4, 5) <= v <= Fraction(6, 5) for v in (v1, v2)),
                label + ' A/A drift exceeds 20%')
        aa[label] = {'original_1_over_2': float(v1), 'reuse_1_over_2': float(v2)}
    for arm in ARMS:
        x = per_call(data[arm], 'C169')
        y = per_call(data[arm], 'C13_first')
        z = per_call(data[arm], 'C13_second')
        vals = [a-b-c for a, b, c in zip(x, y, z)]
        all_deltas.extend(vals)
        paired[arm] = {'block_deltas_ns': [float(v) for v in vals],
                       'median_delta_ns': float(st.median(vals))}
    sign = ('all-positive-component-gap' if all(x > 0 for x in all_deltas) else
            'all-negative-component-gap' if all(x < 0 for x in all_deltas) else
            'mixed-or-zero-inconclusive')
    return {'schema': 'ct142-receipts-and-paired-deltas/v1',
            'standing': '[pcc:unverified]',
            'scope': 'bound live process receipts and warm primitive timing; not a cold ECDLP solve',
            'output_hashes': outputs, 'source_hashes': source, 'binary_hashes': binary,
            'host_sha256': sha(out / 'host.txt'), 'resources': resources,
            'max_aa_drift': 0.20, 'aa': aa, 'paired': paired,
            'all_48_paired_deltas_ns': [float(x) for x in all_deltas], 'sign': sign,
            'inherited_ct126_scope': canonical['status']}


def synthetic(out):
    out.mkdir()
    (out / 'sequence.txt').write_text('\n'.join(SEQUENCE) + '\n')
    (out / 'host.txt').write_text('rustc 1.99.1\ncargo 1.99.1\nSYNTHETIC only\n')
    (out / 'sources').mkdir()
    for name in ('main.rs', 'check_pair.py', 'Cargo.toml', 'reuse-Cargo.toml',
                 'first-lib.rs', 'second-lib.rs', 'ct126-price', 'ct126-price-reuse'):
        (out / 'sources' / name).write_text('synthetic-' + name)
    fixture = check_pair.fixture()
    for arm in ARMS:
        (out / (arm + '.json')).write_text(json.dumps(fixture[arm]))
        (out / (arm + '.stderr')).write_text('')
        (out / (arm + '.exit-status.txt')).write_text('0\n')
        (out / (arm + '.resources.txt')).write_text(
            'Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.10\n'
            'Maximum resident set size (kbytes): 12000\nExit status: 0\n')
    repin(out)


def repin(out):
    src = sorted(p for p in (out / 'sources').iterdir()
                 if p.name not in ('ct126-price', 'ct126-price-reuse'))
    bins = [out / 'sources' / n for n in ('ct126-price', 'ct126-price-reuse')]
    outs = [out / n for n in sorted(EXPECTED_OUTPUTS)]
    for name, paths in (('source-sha256.txt', src), ('binary-sha256.txt', bins),
                        ('outputs-sha256.txt', outs)):
        (out / name).write_text(''.join(sha(p) + '  ' + str(p) + '\n' for p in paths))


def selftest():
    with tempfile.TemporaryDirectory(prefix='ct142-') as tmp:
        p = Path(tmp) / 'fixture'
        synthetic(p)
        require(inspect(p)['schema'] == 'ct142-receipts-and-paired-deltas/v1', 'positive control')
    def test(mutate, repin_after=False):
        with tempfile.TemporaryDirectory(prefix='ct142-') as tmp:
            p = Path(tmp) / 'fixture'
            synthetic(p)
            mutate(p)
            if repin_after:
                repin(p)
            try:
                inspect(p)
            except (ValueError, OSError, ZeroDivisionError):
                return True
            return False
    def edit_json(p, arm, change):
        f = p / (arm + '.json')
        x = json.loads(f.read_text())
        change(x)
        f.write_text(json.dumps(x))
    def replace(p, file, before, after):
        f = p / file
        f.write_text(f.read_text().replace(before, after))
    tests = {
        'changed_stdout_sha': (lambda p: replace(p, 'original-1.json', '223', '224'), False),
        'missing_sha': (lambda p: (p / 'outputs-sha256.txt').write_text('\n'.join((p/'outputs-sha256.txt').read_text().splitlines()[1:])), False),
        'duplicate_sha': (lambda p: (p / 'outputs-sha256.txt').write_text('\n'.join((p/'outputs-sha256.txt').read_text().splitlines()[:-1]+[(p/'outputs-sha256.txt').read_text().splitlines()[0]])+'\n'), False),
        'native_status': (lambda p: (p / 'reuse-1.exit-status.txt').write_text('13\n'), True),
        'missing_elapsed': (lambda p: replace(p, 'reuse-2.resources.txt', 'Elapsed (wall clock) time (h:mm:ss or m:ss): 0:00.10\n', ''), True),
        'excess_rss': (lambda p: replace(p, 'reuse-2.resources.txt', '12000', '3000000'), True),
        'wrong_order': (lambda p: (p / 'sequence.txt').write_text('\n'.join(reversed(SEQUENCE))), False),
        'binary_tamper': (lambda p: (p/'sources'/'ct126-price').write_text('changed!'), False),
        'identity_mutation': (lambda p: edit_json(p, 'original-2', lambda x: x['identity_checks'][0].update(output_public=[777])), True),
        'aa_drift': (lambda p: edit_json(p, 'reuse-2', lambda x: x['timed']['C169'].update(raw_block_ns=[3*y for y in x['timed']['C169']['raw_block_ns']])), True),
        'zero_time': (lambda p: edit_json(p, 'reuse-1', lambda x: x['timed']['D']['raw_block_ns'].__setitem__(0, 0)), True),
        'resource_tamper': (lambda p: replace(p, 'original-2.resources.txt', '12000', '13000'), False),
        'gnu_exit': (lambda p: replace(p, 'reuse-1.resources.txt', 'Exit status: 0', 'Exit status: 1'), True),
    }
    for k, (mutation, fresh_hashes) in tests.items():
        require(test(mutation, fresh_hashes), 'mutation ACCEPTED: ' + k)
    return {'positive': 'passed', 'negative_controls': len(tests),
            'rejected': sorted(tests), 'standing': '[pcc:unverified]'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', nargs='?', type=Path)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(selftest(), sort_keys=True))
        return
    require(args.directory is not None, 'input directory is required')
    result = inspect(args.directory)
    payload = json.dumps(result, sort_keys=True, indent=2) + '\n'
    if args.out:
        require(not args.out.exists(), 'refuse to overwrite earlier CT142 report')
        args.out.write_text(payload)
    print(json.dumps(result, sort_keys=True))

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, ZeroDivisionError) as exc:
        raise SystemExit(str(exc))
