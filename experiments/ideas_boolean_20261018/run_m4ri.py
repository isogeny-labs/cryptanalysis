#!/usr/bin/env python3
"""Existing F5/M4RI engine on immutable small inputs, independently certified."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import resource
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run import write_new, PDP
sys.path.insert(0,str(PDP))
from boolean_m4ri_runner import compute_m4ri_basis


def main(out,inputs):
    out.mkdir(parents=True,exist_ok=False)
    protocol_path=HERE/'m4ri_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    resource.setrlimit(resource.RLIMIT_AS,(protocol['memory_limit_bytes'],)*2)
    write_new(out/'provenance.json',{'argv':sys.argv,'gpu':{'devices':[],'F4_F2_ECHELON':os.environ.get('F4_F2_ECHELON')},
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),protocol_path,inputs,PDP/'boolean_m4ri_runner.py',PDP/'boolean_f5b_m4ri.cpp',PDP/'boolean_f5b_native.cpp']}})
    results=[]
    for case in json.loads(inputs.read_text()):
        for signature_limit in protocol['signature_limits']:
            degree=4 if case['kind']=='chained-S3' else case['nvars']
            result=compute_m4ri_basis(case['nvars'],case['equations'],30,signature_limit,degree,verify=True)
            result.update({'case_id':case['case_id'],'signature_limit':signature_limit,
                           'input_sha256':case['input_sha256'],'matrix_degree':degree})
            write_new(out/f"{case['case_id']}-sig{signature_limit}.json",result)
            print(case['case_id'],signature_limit,result['status'],flush=True)
            results.append(result)
    write_new(out/'results.json',results)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--inputs',type=Path,required=True)
    args=parser.parse_args();main(args.out,args.inputs)
