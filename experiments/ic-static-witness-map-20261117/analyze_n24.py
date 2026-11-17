#!/usr/bin/env python3
"""Check the separate synthetic-unit N24 instruction diagnostic and answers."""
import hashlib,json,re,sys
from pathlib import Path
from callgrind_parser import parse_capture
P=Path(__file__).resolve().parent;ROOT=P.parents[1];D=P/'profile-n24-001'
sys.path.insert(0,str(ROOT/'experiments/fb-archive'))
from purepy import PyField
from external import _smul
summary=json.loads((D/'summary.json').read_text());assert summary['status']=='completed_unqualified' and summary['captures']==4
inst=json.loads((P/'instances.json').read_text())[3];field=inst['field'];curve=inst['curve']
integer=lambda x:int(x,0) if isinstance(x,str) and x.startswith('0x') else int(x)
K=PyField(field['degree'],sum(1<<e for e in field['modulus_exponents']));a=integer(curve['coefficients'][1]);G=tuple(map(integer,curve['generator']))
results=json.loads((D/'results.json').read_text());assert [r['tag'] for r in results]==['compact','packed','indexed','static'];rows=[]
for r in results:
 tag=r['tag'];path=D/(tag+'-inverse.callgrind');assert hashlib.sha256(path.read_bytes()).hexdigest()==r['capture_sha256']
 parsed=parse_capture(path);text=(D/(tag+'-inverse-inclusive-no.stdout')).read_text();match=re.search(r'^\s*([0-9,]+)\s+\([^)]*\)\s+PROGRAM TOTALS',text,re.M);assert match and int(match[1].replace(',',''))==parsed['ir']
 raw=r['result'];answer=raw['report']['Ok']['recovered'];assert raw['curve_id']==inst['curve_id'] and _smul(K,a,G,answer)==tuple(raw['target'])
 selectors={'collector_function':'ic_boundary::collect_and_solve_with','walker_function':'batched_walk::BatchedWalker','pair_probe_function':'ic_boundary::PairTable>::probe','witness_lookup_function':'ic_boundary::PairWitnessMap>::get','generic_dispatch_function':'ic_boundary::decompose_mitm::'}
 groups={name:sum(f['ir'] for f in parsed['functions'] if fragment in f['function']) for name,fragment in selectors.items()}
 assert groups['generic_dispatch_function']==0
 edges=[e for e in parsed['call_edges'] if 'ic_boundary::collect_and_solve_with' in e['callee']]
 lookup_edges=[e for e in parsed['call_edges'] if any(part in e['caller'] or part in e['callee'] for part in ['ic_boundary::PairTable>::probe','ic_boundary::PairWitnessMap>::get','StaticWitnessMap'])]
 rows.append(dict(tag=tag,whole_guest_ir=parsed['ir'],exclusive_sum=parsed['exclusive_sum'],selected_exclusive_function_ir=groups,collector_call_edges=edges,dictionary_and_probe_edges=lookup_edges,top_functions=parsed['functions'][:20],binary_sha256=r['binary_sha256'],answer=answer))
out=dict(status='pass',rows=rows,independent_answer_checks=4,synthetic_units=True,qualification=None,standing='unsigned existing-parser and independent arithmetic invocation',scope='selected exclusive functions and call edges are instruction attribution, not exact collector clocks; no allocator/cache or native-speed causality inferred',source_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),P/'callgrind_parser.py',ROOT/'experiments/fb-archive/purepy.py',ROOT/'experiments/fb-archive/external.py']})
(P/'analysis-n24.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status='pass',answer_checks=4,ir={r['tag']:r['whole_guest_ir'] for r in rows})))
