"""Compare every retained omission line with the full native input; I/O only."""
from pathlib import Path
import hashlib,json,lzma,sys
out=Path(sys.argv[1]);label=sys.argv[2];tags=sys.argv[3:]
assert len(tags)==len(set(tags))and len(tags)in[7,8]
source=out/(label+'-native.txt');rows=[]
for tag in tags:
    omitted=out/(label+'-'+tag+'-entire-actual-records-omitted.txt.xz')
    whole=hashlib.sha256();removed=0;kept=0
    with source.open('rb')as src,lzma.open(omitted,'rb')as actual:
        for line in src:
            if(tag+' ').encode()in line:removed+=1;continue
            assert actual.readline()==line,'omission input changed a retained line'
            whole.update(line);kept+=1
        assert actual.read()==b''
    assert removed>0 and kept>0
    assert not(out/(label+'-'+tag+'-must-not-accept.json')).exists()
    rows.append(dict(tag=tag,removed_lines=removed,retained_lines=kept,compressed_bytes=omitted.stat().st_size,compressed_sha256=hashlib.sha256(omitted.read_bytes()).hexdigest(),whole_decompressed_sha256=whole.hexdigest(),every_retained_line_byte_equal=True))
(out/(label+'-whole-omission-custody.json')).write_text(json.dumps(dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),whole_controls=rows),indent=2)+'\n')
