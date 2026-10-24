"""Direct degree-13 root check of every trace-screened-out source."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF

HERE=Path(__file__).resolve().parent
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H

def sha(path):return sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'sieve_audit_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_DIRECT_SIEVE_AUDIT'
    sources={'auditor':HERE/'audit_sieve.py','result':HERE/'result.json',
             'functions':HERE/'functions.json','hecke11':MODULE}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    saved=json.loads(sources['functions'].read_text())['functions']
    F=GF(20023);funcs={}
    for tag,coeff in saved.items():
        l,part,k=tag.split(':')
        funcs[(int(l),part,int(k))]={tuple(map(int,ab.split(','))):F(v) for ab,v in coeff.items()}
    _,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[13])
    data=json.loads(sources['result'].read_text())
    histogram=Counter();checked=0;exceptions=[]
    for record in data['attempts']:
        if record['status']!='TRACE_OBSTRUCTION':continue
        x,y=record['source'];P=rd.E(0) if x==-1 else rd.E([x,y,1])
        multiplicity=sum(int(m) for _,m in rd.neighbour_x(13,P).roots())
        histogram[multiplicity]+=1;checked+=1
        if multiplicity==14:exceptions.append(record['source'])
    assert checked==data['status_counts']['TRACE_OBSTRUCTION']==16551
    assert not exceptions
    out={'status':'PASS_DIRECT_ROOT_AUDIT_OF_TRACE_EXCLUSIONS',
         'protocol_sha256':sha(HERE/'sieve_audit_protocol.json'),
         'result_sha256':sha(HERE/'result.json'),
         'functions_sha256':sha(HERE/'functions.json'),
         'auditor_sha256':sha(HERE/'audit_sieve.py'),
         'screened_sources_checked':checked,'fully_rational_false_negatives':len(exceptions),
         'rational_root_multiplicity_histogram':dict(histogram)}
    (HERE/'sieve_audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
