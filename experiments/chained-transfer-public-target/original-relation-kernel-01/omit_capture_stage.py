"""Preserve a whole negative-control input with one complete capture stage omitted; I/O only."""
from pathlib import Path
import json,lzma,sys
source,stage,target=sys.argv[1:4]
groups={'available':['available'],'selected':['selected'],'candidate':['kernel','known_logs'],'descent':['descent_starts','descent_splits','recovery']}
assert stage in groups
data=json.loads(Path(source).read_text());calls=data['whole_calls'];assert len(calls)==60
for call in calls:
    for key in groups[stage]:assert key in call;del call[key]
b=json.dumps(data,separators=(',',':')).encode();p=Path(target);assert not p.exists();p.write_bytes(lzma.compress(b));assert lzma.decompress(p.read_bytes())==b
