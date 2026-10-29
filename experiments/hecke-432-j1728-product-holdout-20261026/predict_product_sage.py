"""Freeze j1728 source-fiber counts from rational 27-path j sequences only."""
import importlib.util
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ

HERE=Path(__file__).resolve().parent


def load(path):
    spec=importlib.util.spec_from_file_location('frozen_27_paths',path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def j_at(record,c,field):
    x,y=map(field,c)
    def at(terms):
        return sum((field(QQ(t['coefficient']))*x**t['x_power']*y**t['y_power'] for t in terms),field(0))
    denominator=at(record['denominator'])
    assert denominator
    return int(-at(record['numerator'])/denominator)


def main():
    protocol_path=HERE/'prediction_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_P1439_PRODUCT_PREDICTION'
    for name,rec in protocol['inputs'].items():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256'],name
    factor_result=json.loads(Path(protocol['inputs']['factor_result']['path']).read_text())
    assert factor_result['status']=='MEASURED_UNIT_16_PATH_B_FACTOR'
    factors={cell['factor'] for block in factor_result['primes'].values() for cell in block['cells']}
    assert factors=={1}
    factor=1
    p=protocol['prime'];field=GF(p)
    path_module=load(protocol['inputs']['path_enumerator']['path'])
    source=EllipticCurve(field,[0,0,0,1,0])
    paths=list(path_module.paths(source,3,3))
    assert int(source.j_invariant())==1728%p
    signatures=[tuple([1728%p,*(edge['target_j'] for edge in path)]) for path in paths]
    counts=Counter(signatures)
    coord=json.loads(Path(protocol['inputs']['coordinate']['path']).read_text())
    intermediate=json.loads(Path(protocol['inputs']['intermediate']['path']).read_text())
    rows=json.loads(Path(protocol['inputs']['source_free_rows']['path']).read_text())
    predictions=[]
    for row in rows:
        if row['status']!='VALID':continue
        c=row['C_point']
        signature=tuple(j_at(r,c,field) for r in (coord['source_j'],intermediate['j3'],intermediate['j9'],coord['target_j']))
        if signature[0]!=1728%p:continue
        predictions.append({'C_point':c,'E_point':row['E_point'],'B_point':row['B_point'],
                            'j_sequence':list(signature),'predicted_multiplicity':counts[signature]*factor})
    predictions.sort(key=lambda r:(r['C_point'],r['E_point'],r['B_point']))
    out={'status':'FROZEN_P1439_J1728_PRODUCT_PREDICTION',
         'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
         'source_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'source_model_ainvs':[int(x) for x in source.a_invariants()],
         'prior_measured_16_path_factor':factor,
         'path_j_sequences':[list(x) for x in signatures],
         'path_sequence_histogram':[{'j_sequence':list(seq),'paths':n} for seq,n in sorted(counts.items())],
         'predictions':predictions}
    (HERE/'prediction_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'paths':len(paths),'triples':len(predictions),
                      'predicted_multiplicities':dict(Counter(x['predicted_multiplicity'] for x in predictions))},sort_keys=True))


if __name__=='__main__':main()
