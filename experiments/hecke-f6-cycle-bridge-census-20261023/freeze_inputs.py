"""Freeze all saved conductor-six X0(11) walks before auditing cycle incidence."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'experiments/hecke-floor-overlap-holdout-20261023/tools/hecke11.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files=sorted((ROOT/'experiments').rglob('exp11_class_walk_D*_f6.json'))
    inputs=[]
    for path in files:
        data=json.loads(path.read_text())
        if data.get('f')!=6 or data.get('hecke_primes')!=[2,3]:
            continue
        inputs.append({'path':str(path.relative_to(ROOT)),
                       'sha256':sha(path),
                       'DK':data['DK'],'p':data['p'],'u':data['u'],
                       'class_size':data['class_size'],
                       'relations':data['relations']})
    assert len(inputs)>=14
    result={'status':'FROZEN_RETROSPECTIVE_ALL_SAVED_F6_WALKS',
            'inclusion_rule':'all exp11_class_walk_D*_f6.json under experiments with f=6 and hecke_primes=[2,3], including empty and incomplete legacy outputs',
            'inputs':inputs,
            'hecke_source':str(SOURCE.relative_to(ROOT)),
            'hecke_source_sha256':sha(SOURCE),
            'script_sha256':sha(HERE/'freeze_inputs.py'),
            'candidate_id':None,'timing_claim':None}
    (HERE/'inputs.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'input_count':len(inputs),
                      'zero_classes':sum(row['class_size']==0 for row in inputs)},sort_keys=True))


if __name__=='__main__':main()
