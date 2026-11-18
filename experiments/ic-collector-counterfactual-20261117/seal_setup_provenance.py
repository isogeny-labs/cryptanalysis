#!/usr/bin/env python3
"""Bind the completed runner snapshot to the prepublished identity receipt."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import certifi

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
os.environ['SSL_CERT_FILE'] = certifi.where()
sys.path.insert(0, str(ROOT/'cloud'))
import modal_run as remote

p = argparse.ArgumentParser()
p.add_argument('job')
p.add_argument('--identities-revision', required=True)
a = p.parse_args()
sha = lambda b: hashlib.sha256(b).hexdigest()
volume = remote.volume()
metadata = remote.read_bytes(volume, a.job+'/job.json')
m = json.loads(metadata)
assert metadata == (P/'setup-timing-launch-metadata.json').read_bytes()
assert not m['git']['dirty'] and m['job'] == a.job
status = remote.read_bytes(volume, a.job+'/shards/0/status.json')
assert json.loads(status)['returncode'] == 0
assert json.loads((P/'timing-setup-001/summary.json').read_text())['status'] == 'matrix_completed_unqualified'
snapshot = remote.read_bytes(volume, a.job+'/src.tar.gz')
host = json.loads((P/'timing-setup-001/host.json').read_text())
with tarfile.open(fileobj=io.BytesIO(snapshot), mode='r:gz') as archive:
    for name, value in host['source_sha256'].items():
        raw = archive.extractfile(name).read()
        assert sha(raw) == value
        assert raw == subprocess.check_output(['git', 'show', m['git']['commit']+':'+name], cwd=ROOT)
ids_revision = subprocess.check_output(['git', 'rev-parse', a.identities_revision], cwd=ROOT, text=True).strip()
subprocess.run(['git', 'merge-base', '--is-ancestor', ids_revision, m['git']['commit']], cwd=ROOT, check=True)
for name in ['setup-fresh-identities.json', 'setup-fresh-generation.json']:
    relative = str((P/name).relative_to(ROOT))
    assert (P/name).read_bytes() == subprocess.check_output(['git', 'show', ids_revision+':'+relative], cwd=ROOT)
generation = json.loads((P/'setup-fresh-generation.json').read_text())
assert generation['status'] == 'generated_before_timing'
assert generation['new_candidates'] == 25 and generation['reused_candidates'] == 15
assert generation['fixtures'] == [768, 807] and generation['one_target_workloads'] == 200
arm = json.loads((P/'setup-identity-arm/receipt.json').read_text())
assert generation['identity_probe_sha256_before_and_after'] == arm['binary_sha256']
assert generation['identity_build_receipt_sha256'] == sha((P/'setup-identity-arm/receipt.json').read_bytes())
for name, value in generation['controllers_sha256'].items():
    assert sha((P/name).read_bytes()) == value, 'Frozen controller changed: '+name
binding = dict(status='pass', snapshot_sha256=sha(snapshot), runner_status_sha256=sha(status),
               metadata_sha256=sha(metadata), frozen_source_revision=m['git']['commit'],
               source_files_checked=len(host['source_sha256']), published_identities_revision=ids_revision,
               generation_receipt_sha256=sha((P/'setup-fresh-generation.json').read_bytes()),
               scope='Post-execution binding audit; contemporaneous ARM generation receipt is retained unchanged. No signed performance standing inferred.')
for name, data in [('setup-fresh-native-job-metadata.json', metadata), ('setup-fresh-runner-status.json', status),
                   ('setup-fresh-snapshot-binding.json', (json.dumps(binding, indent=2)+'\n').encode())]:
    path = P/name
    assert not path.exists(), 'Immutable binding exists: '+name
    path.write_bytes(data)
print(json.dumps(binding))
