"""Freeze exact external Hecke class-walk JSON files for branch census."""
from hashlib import sha256
from pathlib import Path
import json
import re

P=Path(__file__).resolve().parent
ROOT=Path('/Volumes/SSD990-2')
PATTERN=re.compile(r'exp11_class_walk_D\d+_f\d+\.json')
SHA=lambda q:sha256(q.read_bytes()).hexdigest()

def main():
    files=sorted(q for q in ROOT.glob('cryptanalysis-hecke-*/**/data/exp11_class_walk_D*_f*.json')
                 if PATTERN.fullmatch(q.name))
    cases=[]
    for q in files:
        d=json.loads(q.read_text())
        assert d['u']*d['u']-4*d['p']==d['DK']*d['f']*d['f']
        cases.append({'path':str(q),'sha256':SHA(q),'p':d['p'],'u':d['u'],
                      'dk':d['DK'],'f':d['f'],'class_size':d['class_size'],
                      'regular_point_present':'(16 : 60 : 1)' in d.get('column_points',[])})
    protocol={'status':'FROZEN_BEFORE_EXTERNAL_SAGE_TRACE_CENSUS',
              'question':'Which sealed external Hecke class walks have the regular j=-121 point in their trace/conductor class but absent from saved columns?',
              'cases':cases,'script_sha256':SHA(P/'external_run.py'),
              'runtime_sha256':SHA(P/'sage_runtime.json'),
              'candidate_id':None,'timing_claim':None}
    (P/'external_protocol.json').write_text(json.dumps(protocol,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':protocol['status'],'cases':len(cases),
                      'unique_primes':len({c['p'] for c in cases}),
                      'protocol_sha256':SHA(P/'external_protocol.json')}))

if __name__=='__main__':main()
