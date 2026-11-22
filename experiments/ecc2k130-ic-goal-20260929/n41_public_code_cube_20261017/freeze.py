"""Freeze all first-slot code cubes without consulting a relation witness."""
import hashlib
import json
import sys
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'n41_sixpair_shared_target_20261017'
sys.path.insert(0,str(OLD))
import circuit


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    g=circuit.geometry();e=circuit.projector()
    q=g['positive_control']['raw_target']
    target=circuit.F.inv(q[0])
    formula,wires,_=circuit.build(target)
    rebuilt=D/'rebuilt_public.xcnf';formula.write(rebuilt)
    original=OLD/'public.xcnf'
    assert sha(rebuilt)==sha(original)
    allowed=sorted({sum(((mask>>bit)&1)<<j for j,bit in enumerate(e['bits']))
                    for mask in g['permitted_canonical_a']})
    assert len(allowed)==40
    mapping={'slot':0,'code_wires':wires['codes'][0],
             'output_wires':wires['outputs'],'allowed_codes':allowed,
             'all_code_wires':wires['codes']}
    (D/'wires.json').write_text(json.dumps(mapping,sort_keys=True,indent=2)+'\n')
    solver=Path('/opt/homebrew/bin/cryptominisat5')
    record={'schema':1,'candidate_id':None,
            'curve_id':'EC1N41Ckb1h7d5e80d3c4d0',
            'public_raw_point':q,
            'source_builder_sha256':sha(OLD/'circuit.py'),
            'archived_formula_sha256':sha(original),
            'rebuilt_formula_sha256':sha(rebuilt),
            'wires_sha256':sha(D/'wires.json'),
            'allowed_codes':allowed,
            'solver_path':str(solver),'solver_sha256':sha(solver),
            'flags':['--threads=1','--maxtime=10','--zero-exit-status',
                     '--verb=1','--printsol=1'],
            'one_cube_parent_cap_s':12,'overall_parent_cap_s':550,
            'rss_cap_bytes':4*1024**3,'worker_count':1,
            'producer_sha256':sha(Path(__file__))}
    (D/'protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'FROZEN','allowed_codes':len(allowed),
                      'formula_sha256':sha(rebuilt),'wires_sha256':sha(D/'wires.json')}))


if __name__=='__main__':main()
