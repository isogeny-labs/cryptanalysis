#!/usr/bin/env python3
"""Bind the immutable preparation receipt, binary and exact Modal metadata bytes."""
import argparse,hashlib,json,os,sys,io,tarfile,subprocess
from pathlib import Path
import certifi
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
os.environ['SSL_CERT_FILE']=certifi.where();sys.path.insert(0,str(ROOT/'cloud'))
import modal_run as remote
from source_manifest import hashes
p=argparse.ArgumentParser();p.add_argument('job');args=p.parse_args()
receipt_path=P/'build-optimized-002/receipt.json';receipt=json.loads(receipt_path.read_text())
assert receipt['status']=='prepared'
assert receipt['source_sha256']['suite/src/cryptanalysis/ic_boundary/batched_walk.rs']==hashes()['suite/src/cryptanalysis/ic_boundary/batched_walk.rs']
binary=P/'build-optimized-002/probe';sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(binary.read_bytes())==receipt['binary_sha256']
metadata_bytes=remote.read_bytes(remote.volume(),args.job+'/job.json');metadata=json.loads(metadata_bytes)
erratum=json.loads((P/'preparation-source-label-erratum.json').read_text())
assert args.job==erratum['job'] and metadata['git']['commit']==erratum['actual_snapshot_commit'] and not metadata['git']['dirty']
assert receipt['source_commit']==erratum['declared_receipt_commit']
snapshot=remote.read_bytes(remote.volume(),args.job+'/src.tar.gz');assert snapshot
with tarfile.open(fileobj=io.BytesIO(snapshot),mode='r:gz') as archive:
 for name in ['suite/src/cryptanalysis/ic_boundary/batched_walk.rs',str((P/'build_optimized.py').relative_to(ROOT))]:
  data=archive.extractfile(name).read()
  exact=subprocess.check_output(['git','show',metadata['git']['commit']+':'+name],cwd=ROOT)
  assert data==exact,'snapshot does not match actual Git commit: '+name
  if name.endswith('batched_walk.rs'):assert sha(data)==receipt['source_sha256'][name]
assert receipt['controlled_source']['baseline_archive_sha256']==json.loads((P/'baseline-source.json').read_text())['sha256']
assert metadata['gpu']=='L4' and metadata['cpu']==4 and metadata['memory_gib']==8
prepared=dict(source_job=args.job,source_commit=metadata['git']['commit'],receipt_source_commit=receipt['source_commit'],binary_sha256=receipt['binary_sha256'],receipt_sha256=sha(receipt_path.read_bytes()),job_metadata_sha256=sha(metadata_bytes),purpose='native correctness preparation; raw source label retained with explicit erratum and full snapshot overlay checks',snapshot_sha256=sha(snapshot),source_label_erratum_sha256=sha((P/'preparation-source-label-erratum.json').read_bytes()))
for path,data in [(P/'optimized-input.json',json.dumps(prepared,indent=2).encode()+b'\n'),(P/'optimized-preparation-job-metadata.json',metadata_bytes)]:
 if path.exists():assert path.read_bytes()==data,'immutable binding differs'
 path.write_bytes(data)
print(json.dumps(prepared))
