#!/usr/bin/env python3
"""CT310 prospective full-695 native producer. Plan-only by default.

Producer-controlled receipts are NOT independently verified execution or PCC.
No AWS access, artifact retrieval or implicit native compilation is performed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import secrets
import socket
import tempfile
import time

import ct304_execution_receipt_gate as audit

CT176_BLOB = '9595589127758b235291449d1c852c8bd13bab92'
MAX_PIPE_BYTES = 4 * 1024 * 1024


def refuse(message):
    raise ValueError('CT310: ' + message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def hex_lock(value, width, name):
    if type(value) is not str or len(value) != width or any(c not in '0123456789abcdef' for c in value):
        refuse('invalid ' + name)
    return value


def number(value, name):
    if type(value) is not int or value <= 0:
        refuse(name + ' must be a positive integer')
    return value


def source_bytes(path):
    return Path(path).read_bytes()


def locked_collector(path):
    if audit.gitblob(source_bytes(path)) != CT176_BLOB:
        refuse('CT176 bounded subprocess source Git blob mismatch')
    spec = importlib.util.spec_from_file_location('ct310_pinned_ct176', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.MAX_CAPTURE != 131072 or not callable(module.bounded_subprocess):
        refuse('CT176 capture code contract differs')
    module.MAX_CAPTURE = MAX_PIPE_BYTES  # Preserve in-flight cap and process-group termination.
    return module


def host():
    if not hasattr(os, 'sched_getaffinity'):
        refuse('CPU affinity is unavailable')
    affinity = sorted(os.sched_getaffinity(0))
    if not affinity:
        refuse('empty CPU affinity')
    return {
        'hostname': socket.gethostname(), 'machine': platform.machine(),
        'system': platform.system(), 'kernel': platform.release(),
        'cpu_affinity': affinity,
    }


def new_file(path, raw):
    with Path(path).open('xb') as fh:
        fh.write(raw)
        fh.flush()
        os.fsync(fh.fileno())


def new_json(path, obj):
    new_file(path, (json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n').encode())


def argv_lock(raw, binary):
    try:
        a = audit.strict_json(raw)
    except (ValueError, TypeError) as exc:
        refuse('malformed JSON argv: ' + str(exc))
    if type(a) is not list or not a or a[0] != str(binary) or any(type(x) is not str or not x for x in a):
        refuse('command must be a string array beginning with the retained binary')
    return a


def custody_lock(path, expected_sha):
    """Producer binds a supplied external receipt, not its independent authenticity."""
    hex_lock(expected_sha, 64, 'custody receipt SHA256')
    raw = source_bytes(path)
    if digest(raw) != expected_sha:
        refuse('model-custody receipt hash mismatch')
    d = audit.strict_json(raw)
    if type(d) is not dict or set(d) != {
        'schema', 'remote', 'sts_preflight_success', 'tool_source_commit',
        'config_git_blob', 'objects', 'owner_approval_reference'
    } or d['schema'] != 'ct310-external-six-object-custody-reference/v1':
        refuse('unsupported custody receipt structure')
    if d['remote'] != 's3' or d['sts_preflight_success'] is not True:
        refuse('STS-first S3 custody not declared')
    hex_lock(d['tool_source_commit'], 40, 'artifact tool commit')
    hex_lock(d['config_git_blob'], 40, 'artifact config Git blob')
    if type(d['owner_approval_reference']) is not str or not d['owner_approval_reference']:
        refuse('missing external owner/provider approval reference')
    v = d['objects']
    if type(v) is not list or len(v) != 6:
        refuse('require six original remotely sourced model objects')
    seen = set()
    for obj in v:
        if type(obj) is not dict or set(obj) != {'key', 'bytes', 'sha256'}:
            refuse('invalid original model object')
        if type(obj['key']) is not str or not obj['key'] or obj['key'] in seen:
            refuse('duplicate or invalid model object key')
        seen.add(obj['key'])
        number(obj['bytes'], 'object byte length')
        hex_lock(obj['sha256'], 64, 'object SHA256')
    return expected_sha


def retain_binary(original, destination, expected_sha):
    """Copy and execute the exact retained bytes; output bundle is replayable."""
    raw = source_bytes(original)
    if digest(raw) != expected_sha:
        refuse('source executable changed before retention')
    new_file(destination, raw)
    destination.chmod(0o700)
    if digest(source_bytes(destination)) != expected_sha:
        refuse('retained executable failed byte-for-byte SHA256 check')
    return destination


def capture_one(role, binary, argv, source_commit, fixture_bytes, root, collector,
                child_seconds, deadline_ns, expected_host):
    if host() != expected_host:
        refuse('host/affinity changed before subprocess')
    remaining = (deadline_ns - time.monotonic_ns()) / 1_000_000_000
    if remaining <= 0:
        refuse('aggregate deadline expired before subprocess')
    timeout = min(remaining, float(number(child_seconds, 'child timeout')))
    exe_hash = digest(source_bytes(binary))
    start = time.perf_counter_ns()
    try:
        code, stdout, stderr, error = collector.bounded_subprocess(argv, timeout)
    except OSError as exc:
        code, stdout, stderr, error = None, b'', str(exc).encode('utf-8', 'backslashreplace'), 'spawn failed'
    wall_ns = time.perf_counter_ns() - start
    out, err = root / (role + '.stdout'), root / (role + '.stderr')
    new_file(out, stdout)
    new_file(err, stderr)
    if digest(source_bytes(binary)) != exe_hash:
        refuse('binary was replaced during capture')
    if host() != expected_host:
        refuse('host/affinity changed after subprocess')
    if error is not None or type(code) is not int or code != 0:
        refuse(role + ' incomplete/nonzero: ' + str(error) + '; exit=' + str(code))
    record = {
        'schema': audit.SCHEMA, 'role': role, 'run_id': secrets.token_hex(16),
        'source_commit_sha': hex_lock(source_commit, 40, 'native source commit'),
        'executable_sha256': exe_hash, 'argv': argv, 'host': expected_host,
        'fixture_git_blob': audit.gitblob(fixture_bytes), 'fixture_sha256': digest(fixture_bytes),
        'exit_code': code, 'timed_out': False, 'capture_complete': True,
        'stdout_sha256': digest(stdout), 'stdout_bytes': len(stdout),
        'stderr_sha256': digest(stderr), 'stderr_bytes': len(stderr),
        'external_wall_ns': max(1, wall_ns), 'peak_rss_kib': None,
    }
    receipt = root / (role + '.receipt.json')
    new_json(receipt, record)
    audit.check_capture(receipt, role, out, err, binary,
                        record['fixture_sha256'], record['fixture_git_blob'])
    return record


def run(args):
    if not args.admission_approved:
        refuse('real execution additionally needs owner/provider approval')
    number(args.timeout_seconds, 'per-child seconds')
    number(args.panel_wall_seconds, 'total panel seconds')
    required = ('fixture','ct176_source','original_executable','reuse_executable',
                'original_sha256','reuse_sha256','original_source_sha','reuse_source_sha',
                'original_argv_json','reuse_argv_json','output_dir',
                'model_custody_receipt','model_custody_sha256')
    if any(getattr(args, x) is None for x in required):
        refuse('two complete binary/fixture/source/custody/command locks required')
    bound_custody = custody_lock(args.model_custody_receipt, args.model_custody_sha256)
    fixture = source_bytes(args.fixture)
    if audit.gitblob(fixture) != audit.FROZEN_BLOB:
        refuse('authentic 48-vector fixture Git blob mismatch')
    original, reuse = args.original_executable, args.reuse_executable
    if original.resolve() == reuse.resolve():
        refuse('two roles require distinct retained executables')
    for binary, expected in ((original,args.original_sha256),(reuse,args.reuse_sha256)):
        if digest(source_bytes(binary)) != hex_lock(expected, 64, 'binary SHA256'):
            refuse('binary differs from frozen digest')
    for value in (args.original_source_sha,args.reuse_source_sha):
        hex_lock(value, 40, 'source commit')
    original_argv = argv_lock(args.original_argv_json, original)
    reuse_argv = argv_lock(args.reuse_argv_json, reuse)
    collector = locked_collector(args.ct176_source)
    machine = host()
    root = args.output_dir.absolute()
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    deadline = time.monotonic_ns() + args.panel_wall_seconds * 1_000_000_000
    new_json(root / 'provenance.json', {
        'schema':'ct310-producer-source-locks/v1', 'ct176_source_git_blob':CT176_BLOB,
        'frozen_fixture_git_blob':audit.FROZEN_BLOB, 'custody_receipt_sha256':bound_custody,
        'external_s3_custody_independently_verified':False,
        'independent_native_execution_verified':False, 'pcc':'unverified'
    })
    try:
        retained_original = retain_binary(original, root/'original.bin', args.original_sha256)
        retained_reuse = retain_binary(reuse, root/'reuse.bin', args.reuse_sha256)
        original_argv = [str(retained_original)] + original_argv[1:]
        reuse_argv = [str(retained_reuse)] + reuse_argv[1:]
        capture_one('original', retained_original, original_argv, args.original_source_sha,
                    fixture, root, collector, args.timeout_seconds, deadline, machine)
        capture_one('reuse', retained_reuse, reuse_argv, args.reuse_source_sha,
                    fixture, root, collector, args.timeout_seconds, deadline, machine)
        result = audit.verify_pair(root/'original.stdout',root/'reuse.stdout',
                    root/'original.stderr',root/'reuse.stderr',retained_original,retained_reuse,
                    root/'original.receipt.json',root/'reuse.receipt.json',args.fixture)
        new_json(root/'admission.json', result)
        new_json(root/'terminal.json', {'schema':'ct310-terminal/v1',
                    'status':'internal_consistency_only', 'pcc':'unverified',
                    'independently_authenticated':False, 'complete_ecdlp_cost':None})
        return result
    except Exception as exc:
        new_json(root/'terminal.json', {'schema':'ct310-terminal/v1','status':'refused',
                    'error':str(exc), 'pcc':'unverified','independently_authenticated':False})
        raise


def self_test():
    """All children and bytes are mock; no native model is executed."""
    class Mock:
        @staticmethod
        def bounded_subprocess(argv, timeout):
            if argv[1] == 'ok': return 0, b'mock-out', b'mock-err', None
            if argv[1] == 'nonzero': return 1, b'incomplete', b'', None
            if argv[1] == 'timeout': return -9, b'partial', b'', 'timeout'
            if argv[1] == 'overflow': return -9, b'x' * 17, b'', 'capture limit exceeded'
            raise AssertionError('unsupported mock case')
    successes, refusals = 0, 0
    with tempfile.TemporaryDirectory(prefix='ct310-source-only-mock-') as d:
        root = Path(d)
        binary = root/'mock-not-executable'
        binary.write_bytes(b'mock only; not a Rust executable')
        fixture = b'not the authentic fixture; no real model'
        machine = host()
        for case in ('ok', 'nonzero', 'timeout', 'overflow'):
            sub = root/case
            sub.mkdir()
            try:
                capture_one('original',binary,[str(binary),case],'a'*40,fixture,
                            sub,Mock(),2,time.monotonic_ns()+2_000_000_000,machine)
                if case != 'ok': raise AssertionError('failed mock admitted')
                successes += 1
            except ValueError:
                if case == 'ok': raise
                if (sub/'original.receipt.json').exists():
                    raise AssertionError('failed mock produced successful receipt')
                refusals += 1
        for argv in ('["wrong"]','{"malformed":true}','[false]'):
            try: argv_lock(argv, binary)
            except ValueError: refusals += 1
            else: raise AssertionError('bad argv accepted')
        try: hex_lock('no',40,'source commit')
        except ValueError: refusals += 1
        else: raise AssertionError('bad commit accepted')
    if (successes, refusals) != (1,7):
        raise AssertionError('CT310 mock controls changed')
    return {'schema':'ct310-source-mock-test/v1','mock_positive':successes,
            'mock_mutations_rejected':refusals,'native_models_executed':0,
            'authenticated_s3_artifacts':0,'pcc':'unverified'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--execute',action='store_true')
    p.add_argument('--admission-approved',action='store_true')
    for name in ('fixture','ct176-source','original-executable','reuse-executable',
                 'output-dir','model-custody-receipt'):
        p.add_argument('--'+name,type=Path)
    for name in ('original-sha256','reuse-sha256','original-source-sha','reuse-source-sha',
                 'original-argv-json','reuse-argv-json','model-custody-sha256'):
        p.add_argument('--'+name)
    p.add_argument('--timeout-seconds',type=int)
    p.add_argument('--panel-wall-seconds',type=int)
    args = p.parse_args()
    if args.self_test:
        if args.execute: refuse('self-test and native execution are mutually exclusive')
        print(json.dumps(self_test(),sort_keys=True))
    elif args.execute:
        print(json.dumps(run(args),sort_keys=True))
    else:
        print(json.dumps({'schema':'ct310-plan-only/v1','native_models_executed':0,
             'requires':'owner/provider admission, valid STS/S3 and six source objects, pinned binaries',
             'pcc':'unverified'},sort_keys=True))


if __name__ == '__main__':
    main()
