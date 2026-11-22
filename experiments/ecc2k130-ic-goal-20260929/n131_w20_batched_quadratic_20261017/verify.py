"""Independent receipt, exact-output, and CPU-accounting audit."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((D/name).read_text())


def main():
    protocol=read('protocol.json')
    cpu_protocol=read('cpu_protocol.json')
    n41_protocol=read('n41_protocol.json')
    n41_result=read('n41_result.json')
    first=read('run_result.json')
    second=read('cpu_result.json')
    assert first['status']==second['status']=='COMPLETE'
    assert first['protocol_sha256']==sha(D/'protocol.json')
    assert second['protocol_sha256']==sha(D/'cpu_protocol.json')
    assert cpu_protocol['prior_result_sha256']==sha(D/'run_result.json')
    assert len(first['rows'])==len(second['rows'])==4
    assert ([(r['implementation'],r['mode']) for r in first['rows']]==
            [tuple(x) for x in protocol['order']])
    assert ([(r['implementation'],r['mode']) for r in second['rows']]==
            [tuple(x) for x in cpu_protocol['order']])
    for item in protocol['sources'].values():
        assert sha(Path(item['path']))==item['sha256']
    assert all(sha(Path(path))==digest for path,digest in n41_protocol['sources'].items())
    assert n41_result['status']=='N41_NORMALIZED_RECURRENCE_CONTROL_PASS'
    assert n41_result['protocol_sha256']==sha(D/'n41_protocol.json')
    assert n41_result['decisions_checked']==5200 and n41_result['gate_hits']==1
    assert n41_result['exceptional_quadratics']==0
    assert n41_result['peak_self_rss_bytes']<n41_protocol['rss_cap_bytes']
    lean=(D/'lean_check.stdout').read_text()
    assert (D/'lean_check.stderr').read_text()==''
    for name in ('linearized_step','normalized_root','initial_normalization',
                 'batch_inverse_step'):
        assert "'NormalizedStep."+name+"' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
    assert 'sorryAx' not in lean
    comparisons=[]
    for pass_name,record in [('abba',first),('reverse',second)]:
        for row in record['rows']:
            imp,mode=row['implementation'],row['mode']
            stem=(f'cpu_{imp}_{mode}' if pass_name=='reverse'
                  else f'{imp}_{mode}')
            output=read(stem+'.json')
            assert row['exit_code']==0 and not row['timed_out']
            assert row['result_sha256']==sha(D/(stem+'.json'))
            assert row['stdout_sha256']==sha(D/(stem+'.stdout'))
            assert row['stderr_sha256']==sha(D/(stem+'.stderr'))
            assert output['status']==('COMPLETE_BATCHED_QUADRATIC_QUERY'
                                      if imp=='batch' else
                                      'COMPLETE_LINEARIZED_QUADRATIC_QUERY')
            assert output['peak_rss_bytes']<protocol['rss_cap_bytes']
            assert output['valid_codes']==132045 and output['left_roots']==264090
            query=output['query']
            assert query['left']==264090 and not query['capped'] and not query['oom']
            if mode=='positive':
                assert output['selected_positive_found']
                assert query['gate_hits']==query['full_span_hits']==1
                assert query['valid_code_hits']==query['distinct_column_hits']==1
                assert len(query['hits'])==1
                assert query['hits'][0]['codes']==[3,16722]
                assert query['hits'][0]['distinct']
            else:
                assert not output['selected_positive_found']
                assert query['gate_hits']==query['full_span_hits']==0
                assert query['valid_code_hits']==query['distinct_column_hits']==0
                assert query['hits']==[]
            comparisons.append({'pass':pass_name,'implementation':imp,'mode':mode,
                                'parent_wall_s':row['parent_wall_s'],
                                'setup_s':output['setup_ns']/1e9,
                                'query_s':output['query_ns']/1e9,
                                'peak_rss_bytes':output['peak_rss_bytes'],
                                'child_user_cpu_s':row.get('child_user_cpu_s'),
                                'child_system_cpu_s':row.get('child_system_cpu_s')})
        for mode in ('positive','ordinary'):
            a=read(('cpu_' if pass_name=='reverse' else '')+'baseline_'+mode+'.json')
            b=read(('cpu_' if pass_name=='reverse' else '')+'batch_'+mode+'.json')
            assert a['query']==b['query']
            assert a['selected_positive_found']==b['selected_positive_found']
    by={(row['implementation'],row['mode']):row for row in second['rows']}
    cpu_ratios={}
    for mode in ('positive','ordinary'):
        baseline=by['baseline',mode]
        batch=by['batch',mode]
        b_cpu=baseline['child_user_cpu_s']+baseline['child_system_cpu_s']
        n_cpu=batch['child_user_cpu_s']+batch['child_system_cpu_s']
        assert b_cpu>n_cpu>0
        cpu_ratios[mode]={'baseline_cpu_s':b_cpu,'batch_cpu_s':n_cpu,
                          'baseline_over_batch':b_cpu/n_cpu}
    audit={'status':'BATCHED_N131_ORACLE_MATCHED_OUTPUT_AUDIT_PASS',
           'protocol_sha256':sha(D/'protocol.json'),
           'cpu_protocol_sha256':sha(D/'cpu_protocol.json'),
           'lean_stdout_sha256':sha(D/'lean_check.stdout'),
           'n41_result_sha256':sha(D/'n41_result.json'),
           'eight_terminal_queries_checked':len(comparisons),
           'rows':comparisons,'cpu_ratios':cpu_ratios}
    (D/'verification.json').write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':audit['status'],'cpu_ratios':cpu_ratios},sort_keys=True))


if __name__=='__main__':
    main()
