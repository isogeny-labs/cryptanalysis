"""Lossless deterministic storage amendment for the frozen raw transcripts."""
from pathlib import Path
import gzip, hashlib, json, math
H=Path(__file__).resolve().parent
R=json.loads((H/'run-result.json').read_text())
files={}
for stem,key,part_count in [('public.jsonl','public_sha256',1),('lifts.jsonl','lifts_sha256',8)]:
    raw=(H/stem).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==R[key]
    lines=raw.splitlines(keepends=True)
    width=math.ceil(len(lines)/part_count)
    parts=[]
    for index in range(part_count):
        chunk=b''.join(lines[index*width:(index+1)*width])
        name=(stem+'.gz') if part_count==1 else f'{stem}.part{index:02d}.gz'
        packed=gzip.compress(chunk,compresslevel=9,mtime=0)
        (H/name).write_bytes(packed)
        assert gzip.decompress((H/name).read_bytes())==chunk
        parts.append({'path':name,'sha256':hashlib.sha256(packed).hexdigest(),
                      'bytes':len(packed),'lines':chunk.count(b'\n')})
    assert b''.join(gzip.decompress((H/z['path']).read_bytes()) for z in parts)==raw
    files[stem]={'raw_sha256':R[key],'raw_bytes':len(raw),'parts':parts}
    (H/stem).unlink()
A={'schema':'xedni-large-order-height-storage-amendment-v2',
   'reason':'Git artifact policy classifies the raw transcripts and a 306250-byte single gzip as store data',
   'compression':'ordered contiguous JSONL chunks; gzip level 9, mtime 0; concatenated decompression reproduces frozen raw bytes exactly',
   'measurement_changed':False,'files':files}
(H/'storage-amendment.json').write_text(json.dumps(A,sort_keys=True,indent=2)+'\n')
print(json.dumps(files,sort_keys=True,indent=2))
