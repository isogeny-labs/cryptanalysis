#!/usr/bin/env python3
"""Validate unit-receipt loading with synthetic units; no attack or timing run."""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('probe',type=Path);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
rows=[];instances=json.loads((P/'instances.json').read_text())
with tempfile.TemporaryDirectory() as tmp:
 for index,instance in enumerate(instances):
  units={k:1.0 for k in ['ns_per_add','ns_per_double','ns_per_lookup','ns_per_row_op']}
  units.update({k:None for k in ['ns_per_sqrt','ns_per_as_solve','ns_per_s4_pair','ns_per_word_xor','ns_per_legendre','ns_per_inversion','ns_per_frobenius','ns_per_canon']});units['pinned_units']=[]
  for case in ['valid_synthetic_units','zero_lookup_rejected','wrong_curve_rejected']:
   doc={'curve_id':instance['curve_id'],'calibration':dict(units)}
   if case=='zero_lookup_rejected':doc['calibration']['ns_per_lookup']=0
   if case=='wrong_curve_rejected':doc['curve_id']='wrong-validation-curve'
   file=Path(tmp)/f'{index}-{case}.json';file.write_text(json.dumps(doc))
   argv=[str(args.probe.resolve()),str(P/'instances.json'),str(index),'calibration','0',str(file)]
   result=subprocess.run(argv,text=True,capture_output=True,timeout=30)
   rows.append(dict(index=index,case=case,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,fixture=doc))
   if case=='valid_synthetic_units':
    assert result.returncode==0 and json.loads(result.stdout)['calibration']==units
   else:assert result.returncode!=0
output=dict(status='pass',purpose='synthetic calibration loader correctness only; no attack or performance measurement',checks=len(rows),rows=rows,binary_sha256=hashlib.sha256(args.probe.read_bytes()).hexdigest())
args.out.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k!='rows'}))
