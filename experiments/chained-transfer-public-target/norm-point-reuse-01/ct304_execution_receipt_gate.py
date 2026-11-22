#!/usr/bin/env python3
"""CT304 read-only paired external-capture receipt and CT302 transcript gate.

A receipt's fields are producer-supplied. Binding them to raw bytes does NOT prove
that a process ran or that a signer authenticated it. No native model runs here.
"""
import argparse
import copy
import hashlib
import json
import re
import tempfile
from pathlib import Path

SCHEMA = 'ct304-bounded-process-receipt/v1'
FROZEN_BLOB = '9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3'
RECEIPT_FIELDS = frozenset((
    'schema', 'role', 'run_id', 'source_commit_sha', 'executable_sha256',
    'argv', 'host', 'fixture_git_blob', 'fixture_sha256', 'exit_code',
    'timed_out', 'capture_complete', 'stdout_sha256', 'stdout_bytes',
    'stderr_sha256', 'stderr_bytes', 'external_wall_ns', 'peak_rss_kib'
))
HOST_FIELDS = frozenset(('hostname', 'machine', 'system', 'kernel', 'cpu_affinity'))
HEX32 = re.compile(r'[0-9a-f]{32}\Z')
HEX40 = re.compile(r'[0-9a-f]{40}\Z')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')


def refuse(message):
    raise ValueError('CT304: ' + message)


def integer(x, name, minimum=0):
    if type(x) is not int or x < minimum:
        refuse(name + ' must be an integer >= ' + str(minimum))
    return x


def digest(data):
    return hashlib.sha256(data).hexdigest()


def gitblob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def strict_json(raw):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                refuse('duplicate JSON key: ' + k)
            d[k] = v
        return d
    def bad_constant(v):
        refuse('nonstandard JSON constant: ' + v)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)


def check_hex(value, pattern, name):
    if type(value) is not str or pattern.fullmatch(value) is None:
        refuse(name + ' must be canonical lowercase hex')


def check_capture(receipt_path, role, stdout_path, stderr_path, executable_path,
                  fixture_sha256, fixture_git_blob=FROZEN_BLOB):
    record = strict_json(receipt_path.read_text(encoding='utf-8'))
    if type(record) is not dict or set(record) != RECEIPT_FIELDS:
        refuse('incorrect receipt schema/fields')
    if record['schema'] != SCHEMA or record['role'] != role:
        refuse('wrong receipt kind or role')
    check_hex(record['run_id'], HEX32, 'run_id')
    check_hex(record['source_commit_sha'], HEX40, 'source_commit_sha')
    for k in ('executable_sha256', 'stdout_sha256', 'stderr_sha256', 'fixture_sha256'):
        check_hex(record[k], HEX64, k)
    if record['fixture_git_blob'] != fixture_git_blob or record['fixture_sha256'] != fixture_sha256:
        refuse('fixture receipt does not match immutable source bytes')
    if type(record['argv']) is not list or not record['argv'] or any(
            type(v) is not str or not v for v in record['argv']):
        refuse('missing exact argv')
    # The capture producer must invoke this exact executable as argv[0].
    if record['argv'][0] != str(executable_path):
        refuse('argv[0] does not name retained executable')
    host = record['host']
    if type(host) is not dict or set(host) != HOST_FIELDS:
        refuse('host identity/affinity fields missing')
    for k in ('hostname', 'machine', 'system', 'kernel'):
        if type(host[k]) is not str or not host[k]:
            refuse('invalid host ' + k)
    affinity = host['cpu_affinity']
    if type(affinity) is not list or not affinity or affinity != sorted(set(
            integer(v, 'affinity', 0) for v in affinity)):
        refuse('invalid host CPU affinity')
    if (type(record['exit_code']) is not int or record['exit_code'] != 0 or
            record['timed_out'] is not False or record['capture_complete'] is not True):
        refuse('non-success, timeout or incomplete/truncated process capture')
    integer(record['external_wall_ns'], 'external_wall_ns', 1)
    if record['peak_rss_kib'] is not None:
        integer(record['peak_rss_kib'], 'peak_rss_kib')
    for label, path, field in (
        ('stdout', stdout_path, 'stdout'),
        ('stderr', stderr_path, 'stderr'),
        ('executable', executable_path, 'executable'),
    ):
        raw = path.read_bytes()
        if digest(raw) != record[field + '_sha256']:
            refuse(label + ' bytes differ from original capture receipt')
        if label != 'executable' and len(raw) != integer(record[label + '_bytes'], label + ' size'):
            refuse(label + ' length differs from receipt')
    return record


def verify_pair(original_log, candidate_log, original_stderr, candidate_stderr,
                original_executable, candidate_executable, original_receipt,
                candidate_receipt, fixture, population_gate=True):
    raw_fixture = fixture.read_bytes()
    blob = gitblob(raw_fixture)
    if blob != FROZEN_BLOB:
        refuse('original immutable fixture Git blob mismatch')
    sha = digest(raw_fixture)
    a = check_capture(original_receipt, 'original', original_log, original_stderr,
                      original_executable, sha, blob)
    b = check_capture(candidate_receipt, 'reuse', candidate_log, candidate_stderr,
                      candidate_executable, sha, blob)
    if a['run_id'] == b['run_id']:
        refuse('two roles reused one process run identifier')
    if a['host'] != b['host']:
        refuse('paired jobs did not preserve exact host and CPU affinity')
    if a['executable_sha256'] == b['executable_sha256']:
        refuse('candidate and original binary are indistinguishable')
    result = None
    if population_gate:
        # Source-only population equality is necessary, not execution proof.
        import ct302_full_native_gate as ct302
        result = ct302.validate(original_log, candidate_log, fixture)
    return {
        'schema': 'ct304-captured-pair-admission/v1',
        'fixture_git_blob': blob,
        'raw_stdout_stderr_hashes_and_lengths_match_receipts': True,
        'retained_executable_hashes_match_receipts': True,
        'receipt_reports_successful_complete_processes': True,
        'paired_host_affinity_matches': True,
        'full_695_and_144_population_consistent': result is not None,
        'native_execution_independently_verified': False,
        'complete_single_target_ecdlp_cost': None,
        'pcc': 'unverified',
        'scope': 'producer-reported receipt/byte consistency; external signed execution and independent arithmetic remain open'
    }


def self_test():
    # Only synthetic receipts and temporary bytes are tested. No native compute.
    with tempfile.TemporaryDirectory(prefix='ct304-synthetic-only-') as folder:
        root = Path(folder)
        fixture = b'not the real fixture - this test cannot enter verify_pair'
        blob = gitblob(fixture)
        files = {}
        for role in ('original', 'reuse'):
            for part in ('stdout', 'stderr', 'executable'):
                files[role, part] = root / (role + '.' + part)
                files[role, part].write_bytes((role + ':' + part).encode())
        def make(role):
            f = files
            return {
                'schema': SCHEMA, 'role': role, 'run_id': ('a' if role == 'original' else 'b')*32,
                'source_commit_sha': ('c' if role == 'original' else 'd')*40,
                'executable_sha256': digest(f[role, 'executable'].read_bytes()),
                'argv': [str(f[role, 'executable']), '--fixed-original-model'],
                'host': {'hostname':'synthetic-host','machine':'x86_64','system':'Linux',
                         'kernel':'synthetic','cpu_affinity':[0, 1]},
                'fixture_git_blob':blob, 'fixture_sha256':digest(fixture),
                'exit_code':0, 'timed_out':False, 'capture_complete':True,
                'stdout_sha256':digest(f[role,'stdout'].read_bytes()),
                'stdout_bytes':len(f[role,'stdout'].read_bytes()),
                'stderr_sha256':digest(f[role,'stderr'].read_bytes()),
                'stderr_bytes':len(f[role,'stderr'].read_bytes()),
                'external_wall_ns':123456, 'peak_rss_kib':None,
            }
        a = make('original')
        p = root / 'receipt.json'
        def trial(r, role='original'):
            p.write_text(json.dumps(r))
            return check_capture(p,role,files[role,'stdout'],files[role,'stderr'],
                                 files[role,'executable'],digest(fixture),blob)
        trial(a)
        cases = []
        def mutate(fn):
            r = copy.deepcopy(a); fn(r); cases.append(r)
        mutate(lambda r:r.update(exit_code=1))
        mutate(lambda r:r.update(exit_code=False))
        mutate(lambda r:r.update(timed_out=True))
        mutate(lambda r:r.update(capture_complete=False))
        mutate(lambda r:r.update(stdout_bytes=r['stdout_bytes']+1))
        mutate(lambda r:r.update(stderr_sha256='0'*64))
        mutate(lambda r:r.update(executable_sha256='f'*64))
        mutate(lambda r:r.update(argv=['/unbound/program']))
        mutate(lambda r:r['host'].update(cpu_affinity=[0,0]))
        mutate(lambda r:r['host'].update(cpu_affinity=[True,1]))
        mutate(lambda r:r.update(run_id='not-a-run-id'))
        mutate(lambda r:r.update(fixture_git_blob='0'*40))
        mutate(lambda r:r.update(peak_rss_kib=True))
        mutate(lambda r:r.update(external_wall_ns=0))
        mutate(lambda r:r.update(extra_field=1))
        for i, sample in enumerate(cases):
            try:
                trial(sample)
            except ValueError:
                continue
            raise AssertionError('CT304 synthetic mutation escaped: '+str(i))
        for malicious in ('{"x":1,"x":1}', '{"x":NaN}', '{"x":Infinity}'):
            try:
                strict_json(malicious)
            except ValueError:
                continue
            raise AssertionError('CT304 bad JSON accepted')
        return {
            'schema':'ct304-synthetic-only-selftest-v1',
            'synthetic_positive':1, 'synthetic_mutations_rejected':len(cases),
            'synthetic_parser_mutations_rejected':3,
            'native_executions':0, 'physical_timings':0, 'pcc':'unverified'
        }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test', action='store_true')
    for arg in ('original','optimized','original-stderr','optimized-stderr',
                'original-executable','optimized-executable','original-receipt',
                'optimized-receipt','fixture'):
        p.add_argument('--'+arg, type=Path)
    a=p.parse_args()
    if a.self_test:
        if any(getattr(a,key.replace('-','_')) is not None for key in (
                'original','optimized','original-stderr','optimized-stderr',
                'original-executable','optimized-executable','original-receipt',
                'optimized-receipt','fixture')):
            p.error('self-test is synthetic and cannot admit external receipts')
        print(json.dumps(self_test(),sort_keys=True)); return
    names=['original','optimized','original_stderr','optimized_stderr',
           'original_executable','optimized_executable','original_receipt',
           'optimized_receipt','fixture']
    if any(getattr(a,k) is None for k in names):
        p.error('CT304 requires both raw logs, both stderr files, executables, receipts and immutable fixture')
    print(json.dumps(verify_pair(*[getattr(a,k) for k in names]), sort_keys=True))


if __name__=='__main__':
    main()
