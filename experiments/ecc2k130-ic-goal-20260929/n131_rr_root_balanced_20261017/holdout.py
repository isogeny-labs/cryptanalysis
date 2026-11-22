"""Evaluate the fixed quadratic certificate on a prospective W23 code."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parity(word):
    return word.bit_count()&1


def main():
    start=time.monotonic()
    protocol=json.loads((D/'eval_protocol.json').read_text())
    assert protocol['producer_sha256']==sha(Path(__file__))
    assert all(sha(Path(path))==digest for path,digest in protocol['sources'].items())
    source=json.loads((D/'holdout_source.json').read_text())
    fit=json.loads((D/'result.json').read_text())
    spec=importlib.util.spec_from_file_location('rr_holdout_balanced',
        ROOT/'n41_n131_sixpair_rr_root_span_20261016'/'run.py')
    rr=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rr)
    field=rr.Field(source['field_degree'],source['field_modulus'])
    linear=int(fit['linear_mask_hex'],16)
    products=[(int(a,16),int(b,16)) for a,b in fit['product_masks_hex']]
    rows=[]
    for root in protocol['first_slot_roots']:
        points=[source['roots'][root][0]]+source['fixed_points']
        coeff=rr.coefficients([p[0] for p in points],
                              [p[1] for p in points],source['target'],field)
        assert coeff is not None
        values=[rr.evaluate(coeff,sign) for sign in protocol['sign_masks']]
        outputs=[]
        for word in values:
            bit=parity(linear&word)
            for a,b in products:
                bit^=parity(a&word)&parity(b&word)
            outputs.append(bit)
        rows.append({'root':root,'coefficient_sha256':hashlib.sha256(json.dumps(coeff).encode()).hexdigest(),
                     'values':values,
                     'zero_signs':[i for i,v in enumerate(values) if v==0],
                     'certificate_one_signs':[i for i,v in enumerate(outputs) if v],
                     'all_signs_excluded':all(outputs)})
    result={'status':'PROSPECTIVE_N131_ROOT_BALANCED_HOLDOUT',
            'protocol_sha256':sha(D/'eval_protocol.json'),
            'source_sha256':sha(D/'holdout_source.json'),
            'certificate_sha256':sha(D/'result.json'),
            'rows':rows,'wall_s':time.monotonic()-start}
    (D/'holdout_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'rows':[
          {'root':row['root'],'zero_count':len(row['zero_signs']),
           'certificate_one_count':len(row['certificate_one_signs']),
           'all_signs_excluded':row['all_signs_excluded']} for row in rows],
          'wall_s':result['wall_s']}))


if __name__=='__main__':
    main()
