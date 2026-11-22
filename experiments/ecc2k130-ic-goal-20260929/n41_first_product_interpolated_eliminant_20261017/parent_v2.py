#!/usr/bin/env sage -python
"""Sequential isolated Sage resultants followed by one small interpolation."""
import argparse,hashlib,json,resource,signal,subprocess,time
from pathlib import Path
from sage.all import GF,PolynomialRing
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
SAGE=Path('/Volumes/SSD990/cryptanalysis/sage')
OLD=ROOT/'n41_twofree_symbolic_resultant_replay_20261016'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main(panel):
    signal.alarm(300)
    proto=json.loads((HERE/'protocol_v2.json').read_text())
    assert panel in proto['panel_order'] and SAGE.is_file()
    files={'parent_v2':HERE/'parent_v2.py','sample_sage':HERE/'sample_sage.py',
           'geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
           'prior':ROOT/'n41_w8_three_pair_resultant_20261013/result.json',
           'witness_archived':OLD/'result.json','negative_archived':OLD/'control_result.json',
           'runtime':HERE/'sage_runtime_info.json'}
    assert proto['source_sha256']=={k:sha(p) for k,p in files.items()}
    rows_dir=HERE/'rows';rows_dir.mkdir(exist_ok=True)
    values=proto['sample_first_products']+proto['holdout_first_products']
    started=time.monotonic_ns();receipts=[]
    for index,pvalue in enumerate(values):
        command=[str(SAGE),'-python',str(HERE/'sample_sage.py'),panel,str(pvalue)]
        begin=time.monotonic_ns()
        child=subprocess.run(command,capture_output=True,text=True,timeout=45)
        elapsed=time.monotonic_ns()-begin
        stem=f'{panel}_{index:02d}_{pvalue}'
        stdout_path=rows_dir/f'{stem}.stdout.txt';stderr_path=rows_dir/f'{stem}.stderr.txt'
        stdout_path.write_text(child.stdout);stderr_path.write_text(child.stderr)
        assert child.returncode==0,(index,child.returncode,child.stderr[-1000:])
        row=json.loads(child.stdout)
        assert row['panel']==panel and row['first_product']==pvalue
        assert row['peak_self_rss_raw']<proto['rss_boundary_bytes']
        receipts.append({'first_product':pvalue,'terms':row['terms'],
                         'resultant_ns':row['resultant_ns'],'launcher_wall_ns':elapsed,
                         'peak_self_rss_raw':row['peak_self_rss_raw'],
                         'stdout_sha256':sha(stdout_path),'stderr_sha256':sha(stderr_path)})
        print(json.dumps({'panel':panel,'sample':index+1,'launcher_s':elapsed/1e9,
                          'child_rss':row['peak_self_rss_raw']}),flush=True)
    built=time.monotonic_ns()
    poly=PolynomialRing(GF(2),'t');t=poly.gen()
    field=GF(2**41,name='t',modulus=t**41+t**3+1)
    def dec(v):return field(poly([(v>>i)&1 for i in range(41)]))
    def enc(v):return sum(int(bit)<<i for i,bit in enumerate(v.polynomial().list()))
    P=PolynomialRing(field,'P')
    samples=[{(i,j):dec(c) for i,j,c in row['terms']} for row in receipts[:17]]
    support=sorted(set().union(*(set(row) for row in samples)))
    tensor={}
    for key in support:
        points=[(dec(p),row.get(key,field.zero()))
                for p,row in zip(proto['sample_first_products'],samples)]
        f=P.lagrange_polynomial(points)
        if f:tensor[key]=f
    assert tensor and max(int(v.degree()) for v in tensor.values())<=16
    interpolation_ns=time.monotonic_ns()-built
    archived=json.loads((OLD/('result.json' if panel=='witness' else 'control_result.json')).read_text())
    holdouts=[]
    for row in receipts[17:]:
        pvalue=row['first_product']
        predicted={(i,j):f(dec(pvalue)) for (i,j),f in tensor.items() if f(dec(pvalue))}
        direct={(i,j):dec(c) for i,j,c in row['terms']}
        assert predicted==direct,(panel,pvalue)
        if pvalue==proto['holdout_first_products'][0]:
            expected={(int(exps[0]),int(exps[1])):dec(c)
                      for exps,c in archived['terms']}
            assert predicted==expected
        holdouts.append({'first_product':pvalue,'terms':len(predicted),'matches_direct':True})
    parent_peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    max_child=max(row['peak_self_rss_raw'] for row in receipts)
    assert parent_peak+max_child<proto['rss_boundary_bytes']
    tensor_rows=[(i,j,[(k,enc(c)) for k,c in enumerate(f.list()) if c])
                 for (i,j),f in sorted(tensor.items())]
    out={'status':'PASS_ISOLATED_FIRST_PRODUCT_INTERPOLATION','panel':panel,
         'candidate_id':None,'curve_id':proto['curve_id'],'protocol_sha256':sha(HERE/'protocol_v2.json'),
         'source_sha256':proto['source_sha256'],'sample_count':17,
         'universal_terms':len(tensor),'max_first_product_degree':max(int(v.degree()) for v in tensor.values()),
         'coefficient_terms':tensor_rows,'holdouts':holdouts,'children':receipts,
         'interpolation_ns':interpolation_ns,'worker_wall_ns':time.monotonic_ns()-started,
         'parent_peak_self_rss_raw':parent_peak,'max_child_peak_self_rss_raw':max_child,
         'combined_rss_upper_bound_bytes':parent_peak+max_child}
    with (HERE/f'{panel}_result_v2.json').open('x') as output:json.dump(out,output,indent=2,sort_keys=True);output.write('\n')
    print(json.dumps({'status':out['status'],'panel':panel,'terms':len(tensor),
                      'worker_s':out['worker_wall_ns']/1e9,'combined_rss_upper_bound':out['combined_rss_upper_bound_bytes']}),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('panel',choices=['witness','negative'])
    main(ap.parse_args().panel)
