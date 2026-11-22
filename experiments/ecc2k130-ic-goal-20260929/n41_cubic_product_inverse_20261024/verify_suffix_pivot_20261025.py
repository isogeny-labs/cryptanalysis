"""Independent archive checks for the frozen N41 suffix-axis follow-up."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PROTOCOL=HERE/'suffix_pivot_protocol_20261025.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads(PROTOCOL.read_text())
    assert protocol['schema']=='n41_suffix_pivot_v1'
    assert protocol['candidate_id'] is None
    for name,expected in protocol['sha256'].items():
        path=HERE/name if not name.startswith('../') else (HERE/name).resolve()
        assert sha(path)==expected,name
    run_rows=[json.loads(line) for line in (HERE/'n41_fouraxis_native_runs_20261025.jsonl').read_text().splitlines()]
    assert len(run_rows)==3
    expected={'status':'PASS_N41_NATIVE_FOUR_AXIS','eligible_triples':42432,
              'eligible_quads':1386816,'first_two_state_sums':24864,
              'first_three_state_sums':2715648,'matches':1,
              'witness':[97,151,42,0,14,109,51]}
    for row in run_rows:
        assert all(row[key]==value for key,value in expected.items())
        assert 0<row['setup_s']<row['wall_s']
        assert 0<row['traversal_s']<row['wall_s']
        assert abs(row['setup_s']+row['traversal_s']-row['wall_s'])<0.00001
    norm=json.loads((HERE/'n41_suffix_norm_result_20261025.json').read_text())
    assert norm['status']=='PASS_N41_SUFFIX_NORM_PILOT'
    assert norm['candidate_id'] is None
    assert (norm['tasks'],norm['source_products'],norm['charts'])==(100,40,160)
    assert norm['retained']==[{'task':0,'degree':1,'hits':[[0,24,37,2,10]]}]
    assert norm['norm_build_s']>0 and norm['gcd_s']>0
    lean=(HERE/'right_quotient_lean_stdout_20261025.txt').read_text()
    stderr=(HERE/'right_quotient_lean_stderr_20261025.txt').read_text()
    assert lean.count('depends on axioms:')==6 and 'sorryAx' not in lean
    assert all(x in lean for x in ('RightQuotient.factor','RightQuotient.composition',
             'RightQuotient.membership','ChartQuartic.chart_A','ChartQuartic.chart_D',
             'ChartQuartic.resultant_simplified'))
    assert 'error:' not in stderr
    runtime=json.loads((HERE/'n41_suffix_norm_sage_runtime_20261025.json').read_text())
    assert runtime['status']=='verified'
    assert runtime['manifest_sha256']=='0a27ddfece04798b893c0feef292caab7f30ce68440f4d18092fe6358ef5499a'
    old=json.loads((ROOT/'n41_four_code_suffix_quotient_20261024/traversal_result.json').read_text())
    assert old['status']=='PASS_N41_FULL_FOUR_AXIS_TRAVERSAL'
    assert (old['eligible_triples'],old['eligible_quads'],old['first_three_state_sums']) == (
           42432,1386816,2715648)
    assert old['matches'][0]['state_ids']==expected['witness']
    # Regenerate the exact native input from frozen source hashes and compare bytes.
    producer=subprocess.run([sys.executable,str(HERE/'n41_fouraxis_native_prepare_20261025.py')],
                            check=True,capture_output=True,text=True)
    produced=json.loads(producer.stdout)
    assert produced['status']=='PASS'
    assert produced['sha256']==sha(HERE/'n41_fouraxis_native_input_20261025.tsv')
    print(json.dumps({'status':'PASS_N41_SUFFIX_PIVOT_ARCHIVE',
                      'native_runs':len(run_rows),'norm_tasks':norm['tasks'],
                      'witness':expected['witness'],'protocol_sha256':sha(PROTOCOL)},sort_keys=True))

if __name__=='__main__':main()
