#!/usr/bin/env python3
"""Bind the immutable preparation receipt, binary and exact Modal metadata bytes."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import certifi
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
os.environ['SSL_CERT_FILE']=certifi.where();sys.path.insert(0,str(ROOT/'cloud'))
import modal_run as remote
from source_manifest import hashes
p=argparse.ArgumentParser();p.add_argument('job');args=p.parse_args()
receipt_path=P/'build-optimized-001/receipt.json';receipt=json.loads(receipt_path.read_text())
assert receipt['status']=='prepared'
assert receipt['source_sha256']['suite/src/cryptanalysis/ic_boundary/batched_walk.rs']==hashes()['suite/src/cryptanalysis/ic_boundary/batched_walk.rs']
binary=P/'build-optimized-001/probe';sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(binary.read_bytes())==receipt['binary_sha256']
metadata_bytes=remote.read_bytes(remote.volume(),args.job+'/job.json');metadata=json.loads(metadata_bytes)
assert metadata['git']['commit']==receipt['source_commit'] and not metadata['git']['dirty']
assert metadata['gpu']=='L4' and metadata['cpu']==4 and metadata['memory_gib']==8
prepared=dict(source_job=args.job,source_commit=metadata['git']['commit'],receipt_source_commit=receipt['source_commit'],binary_sha256=receipt['binary_sha256'],receipt_sha256=sha(receipt_path.read_bytes()),job_metadata_sha256=sha(metadata_bytes),purpose='native correctness preparation only; actual timing allocation requires separate capability admission')
for path,data in [(P/'optimized-input.json',json.dumps(prepared,indent=2).encode()+b'\n'),(P/'optimized-preparation-job-metadata.json',metadata_bytes)]:
 if path.exists():assert path.read_bytes()==data,'immutable binding differs'
 path.write_bytes(data)
print(json.dumps(prepared))
