#!/usr/bin/env python3
"""Six real order layouts through a counted native F5 adapter, exact certificates."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run import write_new, order_layout, OrderedF5, certify_order
from generate_native_orders import generate


def main(out,inputs):
    out.mkdir(parents=True,exist_ok=False)
    source=out/'native-orders.cpp'
    generation=generate(source)
    binary=out/'native-orders'
    build_command=['g++','-O3','-std=c++17',str(source),'-o',str(binary)]
    process=subprocess.run(build_command,capture_output=True,text=True,timeout=60)
    write_new(out/'build.json',{'argv':build_command,'returncode':process.returncode,'stderr':process.stderr,'generation':generation})
    if process.returncode:raise RuntimeError('native build failed')
    write_new(out/'provenance.json',{'argv':sys.argv,'gpu':{'devices':[],'F4_F2_ECHELON':os.environ.get('F4_F2_ECHELON')},
        'scope':'CPU correctness controls, not performance benchmark',
        'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'native_orders_protocol.json',HERE/'protocol.json',HERE/'run.py',HERE/'generate_native_orders.py',inputs,source,binary]}})
    orders=json.loads((HERE/'protocol.json').read_text())['orders']
    records=[]
    for case in json.loads(inputs.read_text()):
        for order in orders:
            equations=[g for g in case['equations'] if g]
            layout,order_record=order_layout(case['nvars'],case['blocks'],order)
            data=f"{case['nvars']} {len(equations)} 100000 -1\n"+' '.join(map(str,layout))+'\n'+''.join(
                f"{len(g)} {' '.join(map(str,g))}\n" for g in equations)
            record={'case_id':case['case_id'],'order':order_record,'input_sha256':case['input_sha256'],'engine':'instrumented-native-Boolean-F5B'}
            try:
                process=subprocess.run([str(binary)],input=data,capture_output=True,text=True,timeout=20)
                record.update({'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
                lines=process.stdout.splitlines()
                if process.returncode or not lines or not lines[0].startswith('OK '):raise RuntimeError('invalid native output')
                head=list(map(int,lines[0].split()[1:]));basis=[list(map(int,row.split()))[1:] for row in lines[1:]]
                names=['basis_size','signature_insertions','reductions','pairs_processed','criterion_calls','criterion_hits','normal_zero_outputs','signature_zero_pairs','product_rows','product_nnz','max_materialized_degree']
                record['counters']=dict(zip(names,head))
                verifier=OrderedF5(case['nvars'],case['blocks'],order,timeout=30,max_pairs=1000000)
                cert=certify_order(equations,basis,verifier)
                record.update({'certificate':cert,'basis':basis,'status':'verified' if cert['verified'] else 'verification-failed'})
            except subprocess.TimeoutExpired as error:
                record.update({'status':'timeout','error':repr(error),'partial_stdout':str(error.stdout),'partial_stderr':str(error.stderr),'counter_status':'not available: killed before final counter record'})
            except BaseException as error:
                record.update({'status':'error','error':repr(error)})
            records.append(record)
            write_new(out/f"{case['case_id']}-{order}.json",record)
            print(case['case_id'],order,record['status'],flush=True)
    write_new(out/'results.json',records)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--inputs',type=Path,required=True)
    args=parser.parse_args();main(args.out,args.inputs)
