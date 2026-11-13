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
    ci,out=map(Path,sys.argv[2:])
    def records(path,prefix):
        rows=[]
        for line in path.read_text().splitlines():
            m=re.search(r'\b('+prefix+r'[A-Z_]+) (\{.*\})$',line)
            if m:rows.append(dict(kind=m[1],data=json.loads(m[2])))
        return rows
    canonical=lambda rows:sorted(json.dumps(x,sort_keys=True,separators=(',',':')) for x in rows)
    v2=records(out/'v2.log','N4_V2_');rho=records(out/'rho.log','N4_RHO_')
    assert len(v2)==7 and len(rho)==5
    assert canonical(v2)==canonical(json.loads((ci/'expected-native-v2.json').read_text()))
    assert canonical(rho)==canonical(json.loads((ci/'expected-native-rho.json').read_text()))
    result=json.loads((out/'rho-five.json').read_text());assert result['ok'] and len(result['results'])==5
    for row,answer in zip(result['results'],[r['data'] for r in rho],strict=True):
        assert row['ok'] and row['original_ok'] and row['independent_original_source_check']
        assert all(row[key]==answer[key] for key in ['target_index','target','seed','k_found','steps','distinguished_points','counters'])
    assert not (out/'reject-scalar.json').exists() and not (out/'reject-witness.json').exists()
    print('All7 V2 and5 rho native records equal frozen originals;actual fiveCLI answers/counters match;two rejected outputs absent. Timing field retained,not compared.')
elif mode=='phases':
    ci,out=map(Path,sys.argv[2:]);rows=[line.split() for line in (out/'phase-index.txt').read_text().splitlines()]
    expected=json.loads((ci/'phase-policy.json').read_text())
    assert [[r[0],int(r[1])] for r in rows]==expected
    assert len(rows)==17 and len({r[0] for r in rows})==17
    for label,status,actual in rows:assert actual==status and (out/(label+'.pipe-exits')).read_text().split()==[actual,'0']
    assert sum(r[1]=='2' for r in rows)==2
    print('All17 orderedphase pairs match:15positive0/0 plus2intentional2/0.')
else:raise SystemExit('unknown I/O mode')
