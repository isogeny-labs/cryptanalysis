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
    ci,out=map(Path,sys.argv[2:]);rows=[]
    for name in ['census.log','replay.log']:
        for line in(out/name).read_text().splitlines():
            m=re.search(r'\b(N4_KERNEL_[A-Z0-9_]+) (\{.*\})$',line)
            if m:rows.append(dict(kind=m[1],data=json.loads(m[2])))
    assert len(rows)==8
    canonical=lambda rows:sorted(json.dumps(x,sort_keys=True,separators=(',',':'))for x in rows)
    assert canonical(rows)==canonical(json.loads((ci/'expected-native.json').read_text()))
    expected=json.loads((ci/'expected-binary.json').read_text());raw=(out/'all-symplectic-matrices.bin').read_bytes()
    assert len(raw)==expected['bytes']and hashlib.sha256(raw).hexdigest()==expected['sha256']
    print('All8 entire native JSON and ALL13063688 original binary bytes/hash match; no exclusions/timing comparison.')
elif mode=='phases':
    ci,out=map(Path,sys.argv[2:]);rows=[line.split()for line in(out/'phase-index.txt').read_text().splitlines()]
    assert [[r[0],int(r[1])]for r in rows]==json.loads((ci/'phase-policy.json').read_text())
    assert len(rows)==15 and len({r[0]for r in rows})==15
    for label,expected,actual in rows:assert expected==actual=='0' and(out/(label+'.pipe-exits')).read_text().split()==['0','0']
    print('All15 ordered native/tee phasepairs0/0.')
else:raise SystemExit('unknown I/O mode')
