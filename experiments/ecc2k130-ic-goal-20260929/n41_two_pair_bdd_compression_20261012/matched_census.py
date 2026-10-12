"""Trace-matched correction to the sampled two-pair output BDD census."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('previous_census', HERE/'census.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
Field = previous.mod.Field
bdd = previous.mod.bdd

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def trace(field, value):
    total = 0
    for _ in range(41):
        total ^= value
        value = field.square(value)
    assert total in (0,1)
    return total

def main():
    field = Field(41,[0,3])
    basis_trace = [trace(field,1<<i) for i in range(41)]
    assert basis_trace == [1]+[0]*40
    with (HERE/'samples.tsv').open() as input_file:
        next(input_file)
        rows = [tuple(map(int,line.split())) for line in input_file]
    assert len(rows)==200000
    assert all((x&1)==0 and (u&1)==0 for _,_,x,u in rows)
    values = [u for _,_,_,u in rows]
    control0 = [int(x) for x in (HERE/'trace_zero.tsv').read_text().splitlines()]
    control1 = [int(x) for x in (HERE/'point_trace_zero.tsv').read_text().splitlines()]
    for control in (control0,control1):
        assert len(control)==len(set(control))==len(values)
        assert all(u and u<1<<41 and (u&1)==0 for u in control)
    for u in control1[:64]:
        assert field.mul(u,field.inverse(u))==1
        assert trace(field,u)==trace(field,field.inverse(u))==0
    records = []
    for count in (25000,50000,100000,200000):
        row = {'count':count}
        for label,group in (('pair',values),('trace_zero',control0),('point_trace_zero',control1)):
            start=time.perf_counter()
            _,nodes=bdd(set(group[:count]),41)
            row[label]={'nodes':len(nodes),'nodes_per_value':len(nodes)/count,
                        'elapsed_s_exploratory':time.perf_counter()-start,
                        'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        row['ratio_pair_to_trace_zero']=row['pair']['nodes']/row['trace_zero']['nodes']
        row['ratio_pair_to_point_trace_zero']=row['pair']['nodes']/row['point_trace_zero']['nodes']
        records.append(row)
        print(json.dumps(row,sort_keys=True),flush=True)
    result={'source_sha256':{name:sha(HERE/name) for name in
             ('samples.tsv','trace_zero.tsv','point_trace_zero.tsv','trace_control.cpp',
              'census.py','matched_census.py')},
            'trace_mask':1,'full_sample_even_x_count':len(rows),
            'full_sample_even_reciprocal_count':len(rows),
            'independent_trace_control_checks':64,'results':records}
    (HERE/'matched_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
