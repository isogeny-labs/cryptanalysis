"""Lossless deterministic storage amendment for the frozen raw transcripts."""
from pathlib import Path
import gzip, hashlib, json
H=Path(__file__).resolve().parent
R=json.loads((H/'run-result.json').read_text())
files={}
for stem,key in [('public.jsonl','public_sha256'),('lifts.jsonl','lifts_sha256')]:
    raw=(H/stem).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==R[key]
    packed=gzip.compress(raw,compresslevel=9,mtime=0)
    gz=H/(stem+'.gz')
    gz.write_bytes(packed)
    assert gzip.decompress(gz.read_bytes())==raw
    files[stem]={'raw_sha256':R[key],'raw_bytes':len(raw),'gzip_sha256':hashlib.sha256(packed).hexdigest(),
                 'gzip_bytes':len(packed),'gzip_path':gz.name}
    (H/stem).unlink()
A={'schema':'xedni-large-order-height-storage-amendment-v1','reason':'Git artifact policy requires the two raw JSONL files above one million bytes to use compact storage','compression':'gzip level 9, mtime 0; decompression reproduces the frozen raw bytes exactly','measurement_changed':False,'files':files}
(H/'storage-amendment.json').write_text(json.dumps(A,sort_keys=True,indent=2)+'\n')
print(json.dumps(files,sort_keys=True,indent=2))
