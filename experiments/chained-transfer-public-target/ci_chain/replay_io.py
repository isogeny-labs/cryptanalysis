"""Only source snapshots, native JSON equality and process-status custody."""
from pathlib import Path
import hashlib,json,re,shutil,sys

mode=sys.argv[1]
if mode=='snapshot':
    repo,producer,out=map(Path,sys.argv[2:])
    for line in (Path(__file__).resolve().parent/'reference-01.sha256').read_text().splitlines():
        expected,relative=line.split('  ',1);source=(repo/relative).resolve()
        assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
        if source.is_relative_to(repo):destination=out/'source/cryptanalysis'/source.relative_to(repo)
        else:
            assert source.is_relative_to(producer);destination=out/'source/crypto'/source.relative_to(producer)
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
elif mode=='outputs':
    ci,out=map(Path,sys.argv[2:]);import lzma
    rows=[]
    for line in(out/'kernels.log').read_text().splitlines():
        m=re.search(r'\b(N4_CHAIN_[A-Z0-9_]+) (\{.*\})$',line)
        if m:rows.append(dict(kind=m[1],data=json.loads(m[2])))
    assert len(rows)==4,len(rows)
    canonical=lambda rows:sorted(json.dumps(x,sort_keys=True,separators=(',',':'))for x in rows)
    assert canonical(rows)==canonical(json.loads(lzma.decompress((ci/'expected-kernels.json.xz').read_bytes())))
    print('ALL4 entire original native JSON exactly equal; no exclusions/timing comparison.')
elif mode=='phases':
    ci,out=map(Path,sys.argv[2:]);rows=[line.split()for line in(out/'phase-index.txt').read_text().splitlines()]
    assert [[r[0],int(r[1])]for r in rows]==json.loads((ci/'phase-policy.json').read_text())
    assert len(rows)==10 and len({r[0]for r in rows})==10
    for label,expected,actual in rows:assert expected==actual=='0' and(out/(label+'.pipe-exits')).read_text().split()==['0','0']
    print('All ten ordered native/tee phasepairs0/0.')
else:raise SystemExit('unknown I/O mode')
