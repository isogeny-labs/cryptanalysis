#!/usr/bin/env python3
"""Two bounded pre-timing development Ir captures of an admitted native binary."""
import argparse, hashlib, json, os, resource, signal, subprocess, sys, tarfile, time
STORAGE_COUNTERS={'mitm_compact_map32_backend','mitm_map_entry_payload_bytes','mitm_vector_packed_square_pairs','mitm_vector_const_packed_square_pairs','mitm_vector_const_validated_pairs','mitm_indexed_prepare_pairs','mitm_static_map32_backend'}
from pathlib import Path
P = Path(__file__).resolve().parent; ROOT = P.parents[1]
parser = argparse.ArgumentParser(); parser.add_argument('--binary', type=Path, required=True); args = parser.parse_args()
D = P/'profile-001'; D.mkdir(exist_ok=False); START = time.monotonic()
summary = {'status': 'started', 'qualified': None}; rows = []
def sha(b): return hashlib.sha256(b).hexdigest()
def limits(): resource.setrlimit(resource.RLIMIT_AS, (32*1024**3, 32*1024**3))
def run(argv, cap, label):
    remaining = 170 - (time.monotonic() - START)
    if remaining <= 0: raise TimeoutError('N27 profile controller cap')
    cap = min(cap, remaining)
    proc = subprocess.Popen(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, preexec_fn=limits)
    started = time.monotonic()
    try: out, err = proc.communicate(timeout=cap); code = proc.returncode
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL); out, err = proc.communicate(); code = 124
    (D/(label+'.stdout')).write_text(out); (D/(label+'.stderr')).write_text(err)
    rows.append({'label': label, 'argv': argv, 'exit_code': code, 'observed_wall_s': time.monotonic()-started})
    (D/'commands.json').write_text(json.dumps(rows, indent=2)+'\n')
    assert code == 0, label
    return out
def signature(raw):
    r = raw['report']['Ok']
    return ([r[s][k] for s,k in [('decomposition','targets_tried'),('decomposition','relations_found'),('linear_algebra','rank'),('linear_algebra','rows'),('linear_algebra','dependent'),('linear_algebra','work')]],
            [(v['group_ops'], {k:x for k,x in v['native'].items() if not k.endswith('_ns') and not k.startswith('walk_batch_inverse_vector_') and k not in STORAGE_COUNTERS}) for v in [r['decomposition']['setup'],r['decomposition']['cost'],r['linear_algebra']['cost'],r['verify']]])
try:
    pin = json.loads((P/'profile-result-input.json').read_text())
    assert sha((Path('/jobs')/pin['job']/'job.json').read_bytes()) == pin['metadata_sha256']
    with tarfile.open(Path('/jobs')/pin['job']/'shards/0/out.tar.gz', 'r:gz') as archive:
        def get(n): return archive.extractfile('experiments/ic-inverse-regression-20261116/profile-001/'+n).read()
        refbytes = get('results.json'); assert sha(refbytes) == pin['results_sha256']; reference = json.loads(refbytes)
        hostbytes = get('host.json'); assert sha(hostbytes) == pin['host_sha256']; oldhost = json.loads(hostbytes)
        cal = get('calibration.json'); assert sha(cal) == pin['calibration_sha256']; (D/'calibration.json').write_bytes(cal)
        walkbytes = get('current-walk.json'); assert sha(walkbytes) == pin['walk_sha256']; oldwalk = json.loads(walkbytes)
    import shutil
    for name in ['valgrind', 'callgrind_annotate', 'objdump']:
        assert sha(Path(shutil.which(name)).read_bytes()) == oldhost['tool_sha256'][name], 'profile tool differs: '+name
    allowed = sorted(os.sched_getaffinity(0)); os.sched_setaffinity(0, {allowed[0]})
    (D/'affinity.json').write_text(json.dumps({'allowed': allowed, 'selected': allowed[0]})+'\n')
    binary = args.binary.resolve(); results = []
    walk = json.loads(run(['valgrind','--tool=none','--log-file='+str(D/'walk.valgrind.log'),str(binary),str(P/'instances.json'),'4','verify-walkbatch','0'],90,'walk-preflight'))
    assert walk['status']=='pass' and walk['checks']==512 and walk['complete_stream_comparisons']==4 and walk['inverse_vector_counters']['walk_batch_inverse_vector_elements']>0
    assert all(walk[k]==oldwalk[k] for k in ['frames','group_ops','curve_id','planted','target','target_seed'])
    (D/'walk.json').write_text(json.dumps(walk,indent=2)+'\n')
    for method, mode, refindex in [('current','mitm-walk16-vector-const',1),('inverse','mitm-walk16-vector-inverse',2)]:
        label='optimized-'+method; capture=D/(label+'.callgrind')
        out=run(['valgrind','--tool=callgrind','--dump-instr=yes','--collect-jumps=yes','--callgrind-out-file='+str(capture),'--log-file='+str(D/(label+'.valgrind.log')),str(binary),str(P/'instances.json'),'4',mode,'0',str(D/'calibration.json')],120,label)
        raw=json.loads(out); ref=reference[refindex]['result']
        assert all(raw[k]==ref[k] for k in ['curve_id','target','target_seed','planted','calibration']) and signature(raw)==signature(ref)
        r=raw['report']['Ok']; assert r['verified'] and r['recovered']==raw['planted']
        q=r['decomposition']['cost']['native']; assert q['walk_batch_vector_pairs']>0
        setup=r['decomposition']['setup']['native']; assert setup['mitm_vector_const_validated_pairs']==setup['mitm_vector_const_packed_square_pairs']==setup['mitm_vector_const_pairs']==setup['mitm_vector_pairs']==setup['mitm_vector_packed_square_pairs']>0
        assert setup['mitm_indexed_prepare_pairs']>=setup['mitm_vector_pairs']>0
        assert setup['mitm_static_map32_backend']==1
        assert r['decomposition']['setup']['native']['mitm_compact_map32_backend']==1 and r['decomposition']['setup']['native']['mitm_map_entry_payload_bytes']==8
        assert (q.get('walk_batch_inverse_vector_elements',0)>0)==(method=='inverse')
        results.append({'method':method,'label':label,'result':raw,'capture_sha256':sha(capture.read_bytes())})
        (D/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        for inclusive in ['no','yes']:
            run(['callgrind_annotate','--auto=no','--threshold=100','--inclusive='+inclusive,str(capture)],20,label+'-inclusive-'+inclusive)
    run(['objdump','-d','-C','--no-show-raw-insn',str(binary)],20,'optimized-disassembly')
    summary.update(status='completed_unqualified',captures=2)
except Exception as error: summary.update(status='failed_or_capped',error=repr(error))
finally: (D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary),flush=True)
if summary['status']!='completed_unqualified': raise SystemExit(1)
