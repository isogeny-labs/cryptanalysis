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



def check_lifetime_inside_external_wall(candidate_log, external_wall_ns):
    """CT309: the seven disjoint CT244 in-process primitive intervals fit wall."""
    marker = 'CT244_PRIMITIVE_TIMING '
    records = [strict_json(line[len(marker):])
               for line in candidate_log.read_text(encoding='utf-8').splitlines()
               if line.startswith(marker)]
    if len(records) != 1:
        refuse('expected one native optimized lifetime timing row')
    slots = records[0].get('elapsed_ns')
    if type(slots) is not list or len(slots) != 7:
        refuse('expected seven primitive lifetime elapsed slots')
    total = sum(integer(v, 'primitive lifetime ns') for v in slots)
    if total > integer(external_wall_ns, 'external wall ns', 1):
        refuse('in-process primitive time exceeds complete external process wall')
    return total

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
    nested_total_ns = None
    if population_gate:
        # Source-only population equality is necessary, not execution proof.
        import ct302_full_native_gate as ct302
        result = ct302.validate(original_log, candidate_log, fixture)
        # CT309: all seven disjoint CT244 lifetime intervals are enclosed by
        # this single optimized native process's external wall duration.
        nested_total_ns = check_lifetime_inside_external_wall(
            candidate_log, b['external_wall_ns'])
    return {
        'schema': 'ct304-captured-pair-admission/v1',
        'fixture_git_blob': blob,
        'raw_stdout_stderr_hashes_and_lengths_match_receipts': True,
        'retained_executable_hashes_match_receipts': True,
        'receipt_reports_successful_complete_processes': True,
        'paired_host_affinity_matches': True,
        'full_695_and_144_population_consistent': result is not None,
        'primitive_lifetime_fits_external_wall': nested_total_ns is not None,
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



def self_test_with_authentic_source(fixture_path):
    """48 genuine selected vectors + 694 synthetic rows and 144 MOCK clocks."""
    import ct302_full_native_gate as ct302
    fixture_bytes = fixture_path.read_bytes()
    original, candidate = ct302.synthetic_pair(fixture_bytes)
    with tempfile.TemporaryDirectory(prefix='ct304-frozen48-synthetic-') as td:
        root = Path(td)
        log_a, log_b = root/'original.log', root/'reuse.log'
        err_a, err_b = root/'original.stderr', root/'reuse.stderr'
        exe_a, exe_b = root/'original.exe', root/'reuse.exe'
        receipt_a, receipt_b = root/'original.json', root/'reuse.json'
        log_a.write_text(original, encoding='utf-8')
        log_b.write_text(candidate, encoding='utf-8')
        err_a.write_bytes(b'synthetic original stderr')
        err_b.write_bytes(b'synthetic reuse stderr')
        exe_a.write_bytes(b'synthetic original executable')
        exe_b.write_bytes(b'synthetic reuse executable')
        paths = [(log_a, err_a, exe_a, receipt_a, 'original', 'a'),
                 (log_b, err_b, exe_b, receipt_b, 'reuse', 'b')]
        def record(stdout, stderr, exe, role, marker):
            return {
                'schema':SCHEMA, 'role':role, 'run_id':marker*32,
                'source_commit_sha':marker*40,
                'executable_sha256':digest(exe.read_bytes()),
                'argv':[str(exe), '--synthetic-no-native'],
                'host':{'hostname':'synthetic-host','machine':'x86_64',
                        'system':'Linux','kernel':'synthetic','cpu_affinity':[0,1]},
                'fixture_git_blob':gitblob(fixture_bytes),
                'fixture_sha256':digest(fixture_bytes), 'exit_code':0,
                'timed_out':False, 'capture_complete':True,
                'stdout_sha256':digest(stdout.read_bytes()),
                'stdout_bytes':len(stdout.read_bytes()),
                'stderr_sha256':digest(stderr.read_bytes()),
                'stderr_bytes':len(stderr.read_bytes()),
                'external_wall_ns':12345, 'peak_rss_kib':0,
            }
        a,b=(record(o,e,x,role,m) for o,e,x,_,role,m in paths)
        def trial(ra=a,rb=b,original_bytes=None,candidate_bytes=None):
            receipt_a.write_text(json.dumps(ra))
            receipt_b.write_text(json.dumps(rb))
            log_a.write_bytes(original.encode() if original_bytes is None else original_bytes)
            log_b.write_bytes(candidate.encode() if candidate_bytes is None else candidate_bytes)
            return verify_pair(log_a,log_b,err_a,err_b,exe_a,exe_b,
                               receipt_a,receipt_b,fixture_path)
        good=trial()
        if not good['full_695_and_144_population_consistent'] or good['native_execution_independently_verified']:
            raise AssertionError('CT304 integrated mock standing changed')
        # CT309: one producer-only positive C169 interval in the first
        # otherwise synthetic sample; the full 695 and 144 scopes stay intact.
        sample_marker = ct302.clocks.SAMPLE
        lifetime_marker = ct302.clocks.LIFETIME
        with_clock = []
        changed_sample = changed_lifetime = False
        for line in candidate.splitlines():
            if line.startswith(sample_marker) and not changed_sample:
                obj = strict_json(line[len(sample_marker):])
                if obj['calls'][4] != 1:
                    raise AssertionError('first CT248 C169 slot changed')
                obj['elapsed_ns'][4] = 20000
                line = sample_marker + json.dumps(obj, sort_keys=True)
                changed_sample = True
            elif line.startswith(lifetime_marker):
                obj = strict_json(line[len(lifetime_marker):])
                obj['elapsed_ns'][4] += 20000
                line = lifetime_marker + json.dumps(obj, sort_keys=True)
                changed_lifetime = True
            with_clock.append(line)
        if not changed_sample or not changed_lifetime:
            raise AssertionError('CT309 synthetic timestamp sources missing')
        timed_candidate = ('\\n'.join(with_clock) + '\\n').encode()
        timed_receipt = copy.deepcopy(b)
        timed_receipt['stdout_sha256'] = digest(timed_candidate)
        timed_receipt['stdout_bytes'] = len(timed_candidate)
        timed_receipt['external_wall_ns'] = 20000
        positive_timed = trial(rb=timed_receipt, candidate_bytes=timed_candidate)
        if not positive_timed['primitive_lifetime_fits_external_wall']:
            raise AssertionError('CT309 positive nested-clock gate failed')

        mutations=[]
        def mut(fn):
            ra,rb=copy.deepcopy(a),copy.deepcopy(b)
            fn(ra,rb)
            mutations.append((ra,rb,None,None))
        mut(lambda ra,rb: rb.update(run_id=ra['run_id']))
        mut(lambda ra,rb: rb['host'].update(cpu_affinity=[2,3]))
        mut(lambda ra,rb: rb.update(executable_sha256=ra['executable_sha256']))
        mut(lambda ra,rb: ra.update(exit_code=True))
        mutations.append((a,b,None,candidate.encode()+b'x'))
        # A producer can forge a matching receipt checksum; the CT302 whole-population
        # gate must still refuse a log with a removed event.
        badlog='\n'.join(original.splitlines()[1:])+'\n'
        forged=copy.deepcopy(a)
        forged['stdout_sha256']=digest(badlog.encode())
        forged['stdout_bytes']=len(badlog.encode())
        mutations.append((forged,b,badlog.encode(),None))
        impossible = copy.deepcopy(timed_receipt)
        impossible['external_wall_ns'] = 19999
        # This forged receipt matches the positive-clock raw stdout hash and
        # all CT302 math/counters; only its external/nested time is impossible.
        mutations.append((a, impossible, None, timed_candidate))
        for i,(ra,rb,oa,ob) in enumerate(mutations):
            try:
                trial(ra,rb,oa,ob)
            except ValueError:
                continue
            raise AssertionError('CT304 frozen-source synthetic mutation escaped: '+str(i))
        return {
            'authentic_source_selected_rows':48,
            'synthetic_other_rows':694,
            'synthetic_zero_ns_clock_samples':144,
            'synthetic_integrated_positive':1,
            'synthetic_clock_nesting_positive':1,
            'synthetic_integrated_mutations_rejected':len(mutations),
            'native_executions':0, 'pcc':'unverified',
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
                'optimized-receipt')):
            p.error('self-test is synthetic and cannot admit external receipts')
        result=self_test()
        if a.fixture is not None:
            result.update(self_test_with_authentic_source(a.fixture))
        print(json.dumps(result,sort_keys=True)); return
    names=['original','optimized','original_stderr','optimized_stderr',
           'original_executable','optimized_executable','original_receipt',
           'optimized_receipt','fixture']
    if any(getattr(a,k) is None for k in names):
        p.error('CT304 requires both raw logs, both stderr files, executables, receipts and immutable fixture')
    print(json.dumps(verify_pair(*[getattr(a,k) for k in names]), sort_keys=True))


if __name__=='__main__':
    main()
