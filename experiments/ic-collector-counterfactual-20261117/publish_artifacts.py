#!/usr/bin/env python3
"""Upload the frozen inventory and report; keep source protocols in Git."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
env = dict(os.environ)
for k in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN',
          'ARTIFACTS_AWS_ACCESS_KEY_ID', 'ARTIFACTS_AWS_SECRET_ACCESS_KEY']:
    env.pop(k, None)
env.update(AWS_PROFILE='default', AWS_REGION='us-west-2', AWS_DEFAULT_REGION='us-west-2',
           ARTIFACTS_REMOTE='s3://crypto-autoresearcher/store', ARTIFACTS_CACHE='/tmp/ic-inverse-regression-cache')
plan = json.loads((P/'raw-reference-plan.json').read_text())
assert len(plan['paths']) == len(set(plan['paths'])) == 25
source = ['PROTOCOL.md', 'FRESH_PROTOCOL.md']
extras = ['REPORT.pdf', 'readback-timing-optimized-001.json',
          'readback-build-001-cell-smoke-001-profile-n24-001.json', 'fresh-snapshot-binding.json',
          'fresh-runner-status.json', 'timing-launch-metadata.json']
extras += [name+'.'+ext for name in ['native-primary', 'native-collector', 'native-setup', 'aa-controls'] for ext in ['svg', 'png']]
names = sorted(set(plan['paths']+extras)-set(source))
assert all((P/n).is_file() for n in names+source)
subprocess.run(['python3', 'tools/artifacts/artifacts.py', 'push', '--jobs', '16',
                *[str((P/n).relative_to(ROOT)) for n in names]], cwd=ROOT, env=env, check=True)
# These two Markdown files are source protocols. Upload their raw copies for
# the record without converting their Git source into artifact pointers.
for name in source:
    path = P/name
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    uri = 's3://crypto-autoresearcher/store/sha256/'+h[:2]+'/'+h
    subprocess.run(['aws', 's3', 'cp', str(path), uri, '--only-show-errors'], env=env, check=True)
print('Published all25raw references and final report artifacts through the scoped working store')
