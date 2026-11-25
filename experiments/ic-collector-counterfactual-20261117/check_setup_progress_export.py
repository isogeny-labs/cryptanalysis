#!/usr/bin/env python3
"""Replay every declared exploratory metric from committed records exactly."""
import argparse, ast, json, subprocess
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[1]
p=argparse.ArgumentParser(); p.add_argument('export',type=Path); p.add_argument('--expected-new',type=int,required=True); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
def show(path): return subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT,text=True)
tree=ast.parse(show('tools/progress_metrics.py'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='ic_native_walk_evidence')
sources=ast.literal_eval(next(n.value for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sources' for t in n.targets)))
actual=[json.loads(line) for line in a.export.read_text().splitlines()]
indexed={r['metric']:r for r in actual}; assert len(indexed)==len(actual)
expected={}; counts={}
for path,problem,prefix,label in sources:
    record=json.loads(show(path)); count=0
    if record['status']=='invalid' and record['problem']==problem:
        for metric in record['metrics']:
            key=prefix+metric['name']; assert key not in expected
            row=indexed[key]
            assert row['value']==float(metric['value']) and row['unit']==metric['unit']
            assert row['better']==metric.get('better','neutral') and row['problem']==problem and row['source']==path
            expected[key]=row; count+=1
    counts[prefix]=count
selected={r['metric'] for r in actual if any(r['metric'].startswith(prefix) for _,_,prefix,_ in sources)}
assert selected==set(expected)
new=counts['ic.collector_buffer.exploratory.']; assert new==a.expected_new
assert sum(counts.values())-new==1444
assert not a.out.exists()
a.out.write_text(json.dumps(dict(status='pass',prior_exact_values=1444,new_exact_values=new,total_exact_values=len(expected),counts=counts,ref=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()),indent=2)+'\n')
print(json.dumps(dict(status='pass',prior_exact_values=1444,new_exact_values=new,total_exact_values=len(expected))))
