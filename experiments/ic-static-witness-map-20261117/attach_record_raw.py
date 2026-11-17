#!/usr/bin/env python3
"""Attach exactly the predeclared 25 working-store raw references."""
import argparse,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[1]
p=argparse.ArgumentParser(); p.add_argument('record',type=Path); a=p.parse_args()
record=a.record.resolve(); assert not json.loads(record.read_text())['raw']
prior=json.loads((ROOT/'benchmarks/records/20261117T0847Z-ic-indexed-pair-sevenpath-001.json').read_text())
names=[Path(row['path']).name.replace('packed-input.json','indexed-input.json') for row in prior['raw']]
names+=['raw-profile-n24-001.tar.gz','profile-n24-001-bundle-receipt.json','analysis-n24.json','packed-input.json']
assert len(names)==len(set(names))==25
for name in names:
    path=P/name; raw=path.read_bytes(); h=hashlib.sha256(raw).hexdigest()
    uri='s3://crypto-autoresearcher/store/sha256/'+h[:2]+'/'+h
    subprocess.run(['python3','tools/benchrec.py','add-raw',str(record),str(path.relative_to(ROOT)),'--s3-uri',uri],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
assert len(json.loads(record.read_text())['raw'])==25
print(json.dumps(dict(status='attached',raw_references=25)))
