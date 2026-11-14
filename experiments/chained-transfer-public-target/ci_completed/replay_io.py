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
    for line in(out/'native.log').read_text().splitlines():
        m=re.search(r'\b(N4_COMPLETED_[A-Z0-9_]+) (\{.*\})$',line)
        if m:rows.append(dict(kind=m[1],data=json.loads(m[2])))
    assert len(rows)==17
    def without_only_timing(records):
        records=json.loads(json.dumps(records))
        for record in records:
            if record['kind']=='N4_COMPLETED_ATTEMPT':
                for method in ['baseline','candidate']:
                    for phase in record['data'][method]['phases']:del phase['wall']
                    record['data'][method]['stats']=[p for p in record['data'][method]['stats']if p[0]!='wall_total']
        return sorted(json.dumps(x,sort_keys=True,separators=(',',':'))for x in records)
    assert without_only_timing(rows)==without_only_timing(json.loads((ci/'expected-native.json').read_text()))
    assert next(x['data']for x in rows if x['kind']=='N4_COMPLETED_FIVE')['candidate_successes']==5
    print('All17 native records equal originalcandidate01 exceptONLYrecordedwall/wall_total;rawtimings retained,no performancecomparison.')
elif mode=='phases':
    ci,out=map(Path,sys.argv[2:]);rows=[line.split()for line in(out/'phase-index.txt').read_text().splitlines()]
    assert [[r[0],int(r[1])]for r in rows]==json.loads((ci/'phase-policy.json').read_text())
    assert len(rows)==5 and len({r[0]for r in rows})==5
    for label,expected,actual in rows:assert expected==actual=='0' and(out/(label+'.pipe-exits')).read_text().split()==['0','0']
    print('All5 ordered native/tee phasepairs0/0.')
else:raise SystemExit('unknown I/O mode')
