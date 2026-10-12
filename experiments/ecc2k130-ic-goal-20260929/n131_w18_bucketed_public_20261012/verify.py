"""Terminal audit of frozen bucket formulas, capped runs, relation, and transfer gate."""
import hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def get(name):return json.loads((HERE/name).read_text())
def main():
    protocol=get('verify_protocol.json')
    paths={k:HERE/v for k,v in protocol['local_files'].items()}
    assert {k:sha(v) for k,v in paths.items()}==protocol['sha256']
    plan=get('bucket_plan.json');assert len(plan['plan'])==8
    geo=json.loads((ROOT/'n41_w7_entropy_cubic_20261011/w8/geometry.json').read_text())
    rows={int(r['mask']):int(r['column']) for r in geo['rows']}
    eligible=set()
    for a,ca in rows.items():
        for b,cb in rows.items():
            if a!=b and ca!=cb:eligible.add((a&63)|((b&63)<<6))
    assert len(eligible)==plan['eligible_bucket_count']==3701
    public=plan['public_target']
    target_bytes=b''.join(int(x).to_bytes(6,'little') for x in public)
    key=lambda b:hashlib.sha256(b'joint-bucket-v1'+target_bytes+b.to_bytes(2,'little')).digest()
    assert [r['bucket'] for r in plan['plan']]==sorted(eligible,key=key)[:8]
    base=(ROOT/'n131_w18_joint_pair_filter_20261012/ordinary.xcnf').read_text().splitlines()
    assert sha(ROOT/'n131_w18_joint_pair_filter_20261012/ordinary.xcnf')==plan['base_formula_sha256']
    for row in plan['plan']:
        lines=(HERE/f"bucket_{row['rank']:02}.xcnf").read_text().splitlines()
        units=[f'{v} 0' for v in row['unit_literals']]
        assert lines[1:13]==units and lines[13:]==base[1:]
        assert sha(HERE/f"bucket_{row['rank']:02}.xcnf")==row['formula_sha256']
    table=get('table_gate_result.json');table_lines=(HERE/'bucket_00_table.xcnf').read_text().splitlines()
    bucket_lines=(HERE/'bucket_00.xcnf').read_text().splitlines()
    assert table_lines[1+table['added_cnf_clauses']:]==bucket_lines[1:]
    assert sha(HERE/'bucket_00_table.xcnf')==table['formula_sha256']
    search=get('search_receipt.json');assert search['status']=='BOUNDED_UNKNOWN'
    assert len(search['attempts'])==8
    for row in search['attempts']:
        i=row['rank'];assert row['bucket']==plan['plan'][i]['bucket']
        assert row['status']=='BOUNDED_UNKNOWN'
        assert sha(HERE/f'bucket_{i:02}.stdout')==row['stdout_sha256']
        assert sha(HERE/f'bucket_{i:02}.stderr')==row['stderr_sha256']
        assert row['solver_terminal_lines']==[s for s in (HERE/f'bucket_{i:02}.stdout').read_text().splitlines() if s.startswith('s ')]
    inc=get('incremental_receipt.json');assert inc['status']=='BOUNDED_UNKNOWN'
    assert inc['stop_reason']=='WALL_CAP' and len(inc['attempts'])==7
    assert all(r['status']=='BOUNDED_UNKNOWN' and r['bucket']==plan['plan'][r['rank']]['bucket'] for r in inc['attempts'])
    assert sha(HERE/'incremental.stdout')==inc['stdout_sha256']
    assert sha(HERE/'incremental.stderr')==inc['stderr_sha256']
    assert get('parser_control_result.json')['status']=='PASS_PYCRYPTOSAT_FULL_MODEL_REPLAY'
    for stem in ('long_bucket','table_solver'):
        r=get(stem+'_receipt.json');assert r['status']=='BOUNDED_UNKNOWN'
        assert r['stop_reason']=='WALL_CAP' and r['bucket']==905
        assert sha(HERE/(stem+'.stdout'))==r['stdout_sha256']
        assert sha(HERE/(stem+'.stderr'))==r['stderr_sha256']
        assert not r['solver_terminal_lines']
    join=get('bucket_join_receipt.json');assert join['status']=='HIT_PENDING_SAGE_AUDIT'
    assert join['stop_reason'] is None and join['exit_code']==0
    assert sha(HERE/'bucket_join.stdout')==join['stdout_sha256']
    assert sha(HERE/'bucket_join.stderr')==join['stderr_sha256']
    hit=join['hit_line'].split();assert hit[:6]==['HIT','1','25126','15330','1757','3290']
    audit=get('bucket_audit_result.json')
    assert audit['status']=='PASS_INDEPENDENT_N41_BUCKET_905_PUBLIC_RELATION'
    assert audit['distinct_folded_columns']==8 and audit['prior_rank']==4
    assert audit['rank_with_four_reference_rows']==5
    assert get('table_control_result.json')['status']=='PASS_N41_BUCKET_TABLE_COMPLETE_ASSIGNMENT'
    projection=get('projection_result.json');pa=get('projection_audit_result.json')
    assert pa['status']=='PASS_INDEPENDENT_N131_BUCKET_LITERAL_MEMORY_AUDIT'
    assert pa['literal_left_entries']==projection['literal_left_entries']==573996287552471808
    assert pa['one_bit_per_entry_bytes']==projection['one_bit_per_entry_bytes']>4294967296
    assert "does not depend on any axioms" in (HERE/'lean_check.txt').read_text()
    result={'status':'PASS_N41_BUCKET_TERMINAL_AUDIT','ordered_buckets':8,
            'verified_public_relation_rank':5,'n131_literal_left_entries':pa['literal_left_entries'],
            'sha256':{k:sha(v) for k,v in paths.items()},
            'protocol_sha256':sha(HERE/'verify_protocol.json')}
    (HERE/'terminal_verification.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],result['verified_public_relation_rank'],flush=True)
if __name__=='__main__':main()
