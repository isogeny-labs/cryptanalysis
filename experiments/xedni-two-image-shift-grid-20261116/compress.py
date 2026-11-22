"""Losslessly split the frozen candidate transcript into policy-sized chunks."""
from pathlib import Path
import gzip,hashlib,json,math
H=Path(__file__).resolve().parent
R=json.loads((H/'run-result.json').read_text())
full=H/'candidates.jsonl.gz'
blob=full.read_bytes()
assert len(blob)==R['candidate_gzip_bytes']
assert hashlib.sha256(blob).hexdigest()==R['candidate_gzip_sha256']
raw=gzip.decompress(blob)
assert hashlib.sha256(raw).hexdigest()==R['candidate_raw_sha256']
lines=raw.splitlines(keepends=True)
assert len(lines)==3969
width=math.ceil(len(lines)/4)
parts=[]
for i in range(4):
    chunk=b''.join(lines[i*width:(i+1)*width])
    packed=gzip.compress(chunk,compresslevel=9,mtime=0)
    path=f'candidates.part{i:02d}.jsonl.gz'
    (H/path).write_bytes(packed)
    assert gzip.decompress((H/path).read_bytes())==chunk
    parts.append({'path':path,'bytes':len(packed),'sha256':hashlib.sha256(packed).hexdigest(),
                  'lines':chunk.count(b'\n')})
assert b''.join(gzip.decompress((H/p['path']).read_bytes()) for p in parts)==raw
A={'schema':'xedni-two-image-shift-storage-amendment-v1',
   'reason':'Git artifact policy classifies the 71395-byte single gzip transcript as store data',
   'compression':'four ordered contiguous JSONL chunks, gzip level 9 mtime 0; concatenated decompression reproduces the frozen raw bytes',
   'measurement_changed':False,'original_gzip_sha256':R['candidate_gzip_sha256'],
   'raw_sha256':R['candidate_raw_sha256'],'parts':parts}
(H/'storage-amendment.json').write_text(json.dumps(A,indent=2,sort_keys=True)+'\n')
full.unlink()
print(json.dumps(A,indent=2,sort_keys=True))
