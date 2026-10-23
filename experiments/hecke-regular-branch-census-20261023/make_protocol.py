"""Freeze all archived exp11 class-walk receipts before trace classification."""
from hashlib import sha256
from pathlib import Path
import json
import re

ROOT=Path('/Volumes/SSD990/cryptanalysis')
P=Path(__file__).resolve().parent
PATTERN=re.compile(r'exp11_class_walk_D\d+_f\d+\.json')
SHA=lambda q:sha256(q.read_bytes()).hexdigest()

def main():
    files=sorted(q for q in (ROOT/'experiments').rglob('exp11_class_walk_D*_f*.json')
                 if PATTERN.fullmatch(q.name))
    cases=[]
    for q in files:
        d=json.loads(q.read_text())
        assert d['u']*d['u']-4*d['p']==d['DK']*d['f']*d['f']
        source=q.parent.parent/'tools/hecke11.py'
        if not source.exists():
            source=q.parent/'hecke11.py'
        if not source.exists():
            source=None
        text='' if source is None else source.read_text()
        cases.append({'path':str(q.relative_to(ROOT)),'sha256':SHA(q),
                      'p':d['p'],'u':d['u'],'dk':d['DK'],'f':d['f'],
                      'class_size':d['class_size'],
                      'regular_point_present_before_census':'(16 : 60 : 1)' in d.get('column_points',[]),
                      'source_path':None if source is None else str(source.relative_to(ROOT)),
                      'source_sha256':None if source is None else SHA(source),
                      'source_has_broad_x16_guard':'if P.is_zero() or P[0] == self.x0' in text})
    protocol={'status':'FROZEN_BEFORE_SAGE_TRACE_CENSUS',
              'question':'For each archived class walk, does the exact regular point (16,60) with j=-121 lie in the frozen trace/conductor class, and was it retained?',
              'cases':cases,'runtime_sha256':SHA(P/'sage_runtime.json'),
              'script_sha256':SHA(P/'run.py'),
              'exact_j_proof_sha256':SHA(ROOT/'experiments/hecke-d1407-f6-20261023/formal/RegularBranch.lean'),
              'candidate_id':None,'timing_claim':None}
    (P/'protocol.json').write_text(json.dumps(protocol,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':protocol['status'],'cases':len(cases),
                      'sources_missing':sum(x['source_path'] is None for x in cases),
                      'protocol_sha256':SHA(P/'protocol.json')}))

if __name__=='__main__':main()
