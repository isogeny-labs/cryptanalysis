#!/usr/bin/env python3
"""Download declared working-store bundles and compare every archived byte."""
import argparse, hashlib, io, json, os, subprocess, tarfile
from pathlib import Path
P = Path(__file__).resolve().parent
a = argparse.ArgumentParser(); a.add_argument('names', nargs='+'); args = a.parse_args()
env = dict(os.environ)
for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'ARTIFACTS_AWS_ACCESS_KEY_ID', 'ARTIFACTS_AWS_SECRET_ACCESS_KEY']:
    env.pop(key, None)
env.update(AWS_PROFILE='default', AWS_REGION='us-west-2', AWS_DEFAULT_REGION='us-west-2')
rows = []
for name in args.names:
    receipt = json.loads((P / (name + '-bundle-receipt.json')).read_text())
    bundle = receipt['bundle']
    raw = subprocess.check_output(['aws', 's3', 'cp', bundle['s3_uri'], '-', '--only-show-errors'], env=env)
    assert len(raw) == bundle['bytes'] and hashlib.sha256(raw).hexdigest() == bundle['sha256']
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        assert sorted(archive.getnames()) == sorted(row['path'] for row in receipt['files'])
        for row in receipt['files']:
            data = archive.extractfile(row['path']).read()
            assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    rows.append(dict(name=name, bytes=len(raw), files=len(receipt['files']), sha256=bundle['sha256']))
out = P / ('readback-' + '-'.join(args.names) + '.json')
assert not out.exists()
out.write_text(json.dumps(dict(status='pass', profile='default', bucket='crypto-autoresearcher', rows=rows), indent=2) + '\n')
print(json.dumps(dict(status='pass', rows=rows)))
