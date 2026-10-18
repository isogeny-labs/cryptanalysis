#!/usr/bin/env python3
"""Order-aware M4RI reference using source-local, provenance-checked adapters."""
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
from run import write_new, order_layout, OrderedF5, certify_order, PDP
from generate_native_orders import generate


def main(out,inputs):
    out.mkdir(parents=True,exist_ok=False)
    engine=out/'native-engine.cpp'
    generated=generate(engine)
    text=engine.read_text();text=text[:text.index('int main(){')]
    engine.write_text(text)
    source=out/'m4ri-orders.cpp'
    original=(PDP/'boolean_f5b_m4ri.cpp').read_text()
    text=original.replace('#include "boolean_f5b_native.cpp"','#include "native-engine.cpp"')
    anchor='    Engine engine(n, signature_limit, -1);'
    if text.count(anchor)!=1:raise ValueError('main constructor drift')
    text=text.replace(anchor,anchor+'''
    for(unsigned j=0;j<unsigned(engine.universe);++j){unsigned mask;std::cin>>mask;if(mask>=unsigned(engine.universe))return 3;engine.mask_by_rank[j]=mask;engine.rank_by_mask[mask]=j;}
''')
    anchor='        F.push_back(polynomial);'
    if text.count(anchor)!=1:raise ValueError('input anchor drift')
    text=text.replace(anchor,'        engine.max_materialized_degree=std::max(engine.max_materialized_degree,engine.degree(polynomial));\n'+anchor)
    anchor='              << stats.f5_rows << " " << stats.f5_remainders << "\\n";'
    if text.count(anchor)!=1:raise ValueError('output anchor drift')
    text=text.replace(anchor,'''              << stats.f5_rows << " " << stats.f5_remainders << " "
              << engine.criterion_calls << " " << engine.criterion_hits << " "
              << engine.normal_zero_outputs << " " << engine.signature_zero_pairs << " "
              << engine.product_rows << " " << engine.product_nnz << " "
              << engine.max_materialized_degree << " " << engine.reductions << "\\n";''')
    source.write_text(text)
    prefix=Path(os.environ['M4RI_PREFIX'])
    binary=out/'m4ri-orders'
    build_command=['g++','-O3','-std=c++17','-I'+str(prefix/'include'),str(source),'-L'+str(prefix/'lib'),'-lm4ri','-o',str(binary)]
    process=subprocess.run(build_command,capture_output=True,text=True,timeout=60)
    write_new(out/'build.json',{'argv':build_command,'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr,'generator':generated})
    if process.returncode:raise RuntimeError('native build failed')
    write_new(out/'provenance.json',{'argv':sys.argv,'gpu':{'devices':[],'F4_F2_ECHELON':os.environ.get('F4_F2_ECHELON')},
        'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'m4ri_orders_protocol.json',HERE/'run.py',inputs,source,engine,binary,prefix/'lib/libm4ri.a',PDP/'boolean_f5b_m4ri.cpp']}})
    resource.setrlimit(resource.RLIMIT_AS,(1610612736,)*2)
    records=[]
    for case in json.loads(inputs.read_text()):
        for order in json.loads((HERE/'protocol.json').read_text())['orders']:
            equations=[g for g in case['equations'] if g]
            degree=4 if case['kind']=='chained-S3' else case['nvars']
            layout,order_record=order_layout(case['nvars'],case['blocks'],order)
            data=f"{case['nvars']} {len(equations)} 0 {degree}\n"+' '.join(map(str,layout))+'\n'+''.join(
                f"{len(g)} {' '.join(map(str,g))}\n" for g in equations)
            record={'case_id':case['case_id'],'order':order_record,'input_sha256':case['input_sha256'],'matrix_degree':degree,'matrix_columns_allocated':1 << case['nvars']}
            try:
                process=subprocess.run([str(binary)],input=data,capture_output=True,text=True,timeout=30)
                record.update({'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
                lines=process.stdout.splitlines()
                if process.returncode or not lines or not lines[0].startswith('OK '):raise RuntimeError('invalid native output')
                head=lines[0].split()[1:]
                names=['basis_size','diagnostic_unisolated_seconds','signature_insertions','signature_pairs_processed','diagnostic_signature_seconds','matrix_rows','matrix_rank','diagnostic_generation_seconds','diagnostic_population_seconds','diagnostic_elimination_seconds','diagnostic_completion_seconds','f5_rows','f5_remainders','criterion_calls','criterion_hits','normal_zero_outputs','signature_zero_pairs','product_rows','product_nnz','max_materialized_degree','reductions']
                record['counters']={name:float(value) if name.startswith('diagnostic') else int(value) for name,value in zip(names,head)}
                basis=[list(map(int,row.split()))[1:] for row in lines[1:]]
                verifier=OrderedF5(case['nvars'],case['blocks'],order,timeout=30,max_pairs=1000000)
                cert=certify_order(equations,basis,verifier)
                record.update({'certificate':cert,'basis':basis,'status':'verified' if cert['verified'] else 'verification-failed'})
            except subprocess.TimeoutExpired as error:record.update({'status':'timeout','error':repr(error)})
            except BaseException as error:record.update({'status':'error','error':repr(error)})
            records.append(record)
            write_new(out/f"{case['case_id']}-{order}.json",record)
            print(case['case_id'],order,record['status'],flush=True)
    write_new(out/'results.json',records)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--inputs',type=Path,required=True)
    args=parser.parse_args();main(args.out,args.inputs)
