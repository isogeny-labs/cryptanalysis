"""Read-only audit of the exhaustive bounded public-target cube partition."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'n41_sixpair_shared_target_20261017'
GEO=D.parent/'n41_w8_fixed_sum_table_20261009'/'geometry.json'


def read(path):return json.loads(path.read_text())


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def main():
    p=read(D/'protocol.json');rp=read(D/'run_protocol.json')
    pilot=read(D/'pilot_result.json');campaign=read(D/'campaign_result.json')
    mapping=read(D/'wires.json')
    base=(D/'rebuilt_public.xcnf').read_bytes()
    assert sha(OLD/'public.xcnf')==sha(D/'rebuilt_public.xcnf')==p['rebuilt_formula_sha256']
    assert sha(OLD/'circuit.py')==p['source_builder_sha256']
    assert sha(D/'freeze.py')==p['producer_sha256']
    assert sha(D/'wires.json')==p['wires_sha256']
    assert sha(Path(p['solver_path']))==p['solver_sha256']
    assert sha(D/'protocol.json')==rp['protocol_sha256']==campaign['protocol_sha256']
    assert sha(D/'run.py')==rp['runner_sha256']
    assert sha(D/'sage_runtime_info.json')==rp['runtime_info_sha256']
    assert sha(D/'run_protocol.json')==campaign['run_protocol_sha256']
    assert mapping['slot']==0 and mapping['allowed_codes']==p['allowed_codes']
    assert len(mapping['code_wires'])==7
    geometry=read(GEO)
    bits=[i for i in range(8) if i!=geometry['fixed_seed_sum_code'].bit_length()-1]
    independently_allowed=sorted({sum(((mask>>bit)&1)<<j for j,bit in enumerate(bits))
                                  for mask in geometry['permitted_canonical_a']})
    assert independently_allowed==p['allowed_codes'] and len(independently_allowed)==40
    source_lines=set(base.decode().splitlines())
    for code in set(range(128))-set(independently_allowed):
        clause=' '.join(str(-wire if code>>j&1 else wire)
                        for j,wire in enumerate(mapping['code_wires']))+' 0'
        assert clause in source_lines,code
    first,tail=base.split(b'\n',1)
    tag,kind,nvars,nclauses=first.decode().split()
    assert (tag,kind)==('p','cnf')
    assert campaign['status']=='ALL_CUBES_BOUNDED_OR_UNCERTIFIED'
    assert campaign['completed_codes']==independently_allowed
    assert pilot['status']=='PARTIAL' and pilot['completed_codes']==independently_allowed[:1]
    rows=[]
    for code in independently_allowed:
        stem=f'cube_{code:03d}'
        r=read(D/(stem+'_result.json'))
        units=''.join(f"{wire if code>>j&1 else -wire} 0\n"
                      for j,wire in enumerate(mapping['code_wires'])).encode()
        expected=f'p cnf {nvars} {int(nclauses)+7}\n'.encode()+tail+units
        formula=D/(stem+'.xcnf')
        assert formula.read_bytes()==expected
        assert sha(formula)==r['input_sha256']
        assert sha(D/(stem+'_result.json'))==campaign['result_sha256'][str(code)]
        assert r['code']==code and r['protocol_sha256']==campaign['protocol_sha256']
        assert r['run_protocol_sha256']==campaign['run_protocol_sha256']
        assert r['command']==[p['solver_path'],*p['flags'],str(formula)]
        for ext in ('stdout','stderr'):
            assert sha(D/(stem+'.'+ext))==r[ext+'_sha256']
        log=(D/(stem+'.stdout')).read_text()
        assert 'Reading file' in log and 'c Parsing time:' in log
        assert r['restart_lines']==sum(line.startswith('c rst ') for line in log.splitlines())>0
        assert r['terminal_lines']==[line for line in log.splitlines() if line.startswith('s ')]==[]
        assert r['status']=='BOUNDED_UNKNOWN' and r['stop_reason']=='PARENT_WALL_CAP'
        assert r['exit_code']==-15 and not r['monitor_degraded']
        assert r['wall_s']>=p['one_cube_parent_cap_s']
        assert r['sampled_peak_combined_rss_bytes']<p['rss_cap_bytes']
        rows.append(r)
    wall=sum(r['wall_s'] for r in rows)
    assert abs(wall-campaign['sum_cube_wall_s'])<1e-6
    assert wall<p['overall_parent_cap_s']
    witness_protocol=read(D/'witness_protocol.json')
    witness=read(D/'witness_result.json')
    archive=read(OLD/'join_audit_result.json')
    assert witness_protocol['campaign_result_sha256']==sha(D/'campaign_result.json')
    assert witness_protocol['producer_sha256']==sha(D/'witness_control.py')
    assert witness_protocol['archive_sha256']==sha(OLD/'join_audit_result.json')
    assert sha(D/'witness_protocol.json')==witness['protocol_sha256']
    assert witness['status']=='PASS_PUBLIC_WITNESS_ASSIGNMENT'
    assert witness['assignment_check']=={'clauses':82957,'native_xor_rows':3689}
    assert witness['raw_target']==archive['raw_target']==p['public_raw_point']
    assert witness['first_code']==witness_protocol['retrospective_witness_code']
    assert read(D/f"cube_{witness['first_code']:03d}_result.json")['status']=='BOUNDED_UNKNOWN'
    assert (D/'lean_build.exit').read_text().strip()=='0'
    assert 'CubePartition.exactAllowedPartition' in (D/'lean_build.stdout').read_text()
    result={'status':'PASS_CENSORED_PARTITION_AUDIT',
            'allowed_cubes':len(rows),'bounded_cubes':len(rows),
            'sum_cube_wall_s':wall,
            'peak_combined_rss_bytes':max(r['sampled_peak_combined_rss_bytes'] for r in rows),
            'sum_restart_lines':sum(r['restart_lines'] for r in rows),
            'retrospective_satisfiable_code':witness['first_code'],
            'retrospective_satisfiable_code_status':'BOUNDED_UNKNOWN'}
    (D/'verification.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
