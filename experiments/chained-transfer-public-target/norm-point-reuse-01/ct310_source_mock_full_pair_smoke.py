#!/usr/bin/env python3
"""Source-only CT310 -> CT304 complete capture handshake, never native math.

Authentic frozen 48 selected SOURCE rows plus 694 fabricated other rows,
144 mock zero-ns clocks, and two harmless Python script subprocesses.
Even a passing result is NOT a physical 695 native-model run, PCC, or ECDLP.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

import ct302_full_native_gate as ct302
import ct310_bounded_native_pair_producer as ct310


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make_script(path, log_text):
    # Exact producer-emitted transcript from CT302.synthetic_pair, never Rust.
    raw = ("#!/usr/bin/env python3\n"
           "import sys\n"
           "sys.stdout.buffer.write(" + repr(log_text.encode('utf-8')) + ")\n").encode('utf-8')
    path.write_bytes(raw)
    path.chmod(0o700)
    return sha(raw)


def smoke(fixture, collector_source):
    fixture_bytes = fixture.read_bytes()
    if ct310.audit.gitblob(fixture_bytes) != ct310.audit.FROZEN_BLOB:
        raise ValueError('CT310 source mock must use immutable authentic 48-row source')
    original, reuse = ct302.synthetic_pair(fixture_bytes)
    with tempfile.TemporaryDirectory(prefix='ct310-full-mock-only-') as td:
        root = Path(td)
        bin_a, bin_b = root/'mock-original.py',root/'mock-reuse.py'
        hash_a, hash_b = make_script(bin_a, original), make_script(bin_b, reuse)
        # The externally supplied *mock* reference is intentionally not signed,
        # not remotely retrieved and not evidence that AWS STS ever succeeded.
        record = {'schema':'ct310-external-six-object-custody-reference/v1',
                  'remote':'s3','sts_preflight_success':True,
                  'tool_source_commit':'a'*40,'config_git_blob':'b'*40,
                  'owner_approval_reference':'SYNTHETIC-SOURCE-TEST-NOT-APPROVAL',
                  'objects':[{'key':'SYNTHETIC_ONLY_'+str(i),
                              'bytes':i+1,'sha256':('%064x' % i)}
                             for i in range(6)]}
        custody = root/'synthetic_custody.json'
        custody.write_text(json.dumps(record),encoding='utf-8')
        kw = dict(fixture=fixture,ct176_source=collector_source,
                  original_executable=bin_a,reuse_executable=bin_b,
                  original_sha256=hash_a,reuse_sha256=hash_b,
                  original_source_sha='a'*40,reuse_source_sha='b'*40,
                  original_argv_json=json.dumps([str(bin_a)]),
                  reuse_argv_json=json.dumps([str(bin_b)]),
                  output_dir=root/'accepted',model_custody_receipt=custody,
                  model_custody_sha256=sha(custody.read_bytes()),
                  admission_approved=True,timeout_seconds=10,panel_wall_seconds=30)
        result = ct310.run(SimpleNamespace(**kw))
        if (result['full_695_and_144_population_consistent'] is not True or
            result['native_execution_independently_verified'] is not False or
            result['complete_single_target_ecdlp_cost'] is not None or
            result['pcc'] != 'unverified'):
            raise AssertionError('producer mock result acquired real scientific standing')
        stored = root/'accepted'
        for name in ('original.bin','reuse.bin','original.stdout','reuse.stdout',
                     'original.stderr','reuse.stderr','original.receipt.json',
                     'reuse.receipt.json','admission.json','terminal.json'):
            if not (stored/name).exists():
                raise AssertionError('missing exact source custody: '+name)
        if (stored/'original.stdout').read_bytes() != original.encode('utf-8'):
            raise AssertionError('original producer changed bytes')
        if (stored/'reuse.stdout').read_bytes() != reuse.encode('utf-8'):
            raise AssertionError('reuse producer changed bytes')
        if json.loads((stored/'terminal.json').read_text())['status'] != 'internal_consistency_only':
            raise AssertionError('mock producer mislabeled scientific standing')

        # A second full capture with one fabricated event missing must retain
        # both receipts and an explicit refusal, not promote a subset as native.
        bad_a = root/'mock-bad-original.py'
        make_script(bad_a, original)
        bad_b = root/'mock-bad-reuse.py'
        corrupted_reuse = '\n'.join(reuse.splitlines()[1:])+'\n'
        bad_hash_b = make_script(bad_b, corrupted_reuse)
        rejected_kw = dict(kw, original_executable=bad_a,
                           reuse_executable=bad_b,
                           original_sha256=sha(bad_a.read_bytes()),
                           reuse_sha256=bad_hash_b,
                           original_argv_json=json.dumps([str(bad_a)]),
                           reuse_argv_json=json.dumps([str(bad_b)]),
                           output_dir=root/'rejected')
        try:
            ct310.run(SimpleNamespace(**rejected_kw))
        except (ValueError,TypeError,KeyError):
            pass
        else:
            raise AssertionError('corrupted 695 mock admitted')
        if (root/'rejected'/'admission.json').exists():
            raise AssertionError('corrupted mock promoted to admission')
        if json.loads((root/'rejected'/'terminal.json').read_text())['status'] != 'refused':
            raise AssertionError('failed mock missing refusal terminal')
        return {'schema':'ct310-source-only-full-handshake/v1',
                'original_selected_authentic_rows':48,
                'synthetic_other_rows':694,
                'synthetic_scoped_clocks':144,
                'producer_auditor_mock_acceptances':1,
                'mutated_full_log_mock_rejections':1,
                'benign_python_child_processes':4,
                'original_native_model_executions':0,
                'physical_primitive_prices':0,
                'ecdlp_complete_solve':False,
                'pcc':'unverified'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixture',type=Path,required=True)
    p.add_argument('--ct176-source',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(smoke(a.fixture,a.ct176_source),sort_keys=True))
