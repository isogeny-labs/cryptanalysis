"""Frozen held-out analysis of native clocks/counters; no curve arithmetic."""
from pathlib import Path
import hashlib,json,math,random,statistics,sys
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def geometric(v):return math.exp(sum(math.log(x) for x in v)/len(v))
def interval(ratios):
    rng=random.Random(1729);logs=[math.log(x) for x in ratios]
    draws=sorted(math.exp(sum(rng.choice(logs) for _ in logs)/len(logs)) for _ in range(10000))
    return [draws[249],draws[9749]]
def main():
    m=json.loads((HERE/'manifest.json').read_text());assert len(m['cells'])==46
    assert sha(HERE/'PROTOCOL.md')==m['protocol_sha256'] and sha(HERE/'seeds.json')==m['seeds_sha256']
    for c in m['cells']:
        assert sha(HERE/'raw'/(c['id']+'.txt'))==c['log_sha256']
        if c['stage']!='rho' and c['report'] is not None:assert sha(HERE/'raw'/(c['id']+'.json'))==c['report_sha256']
    held=[c for c in m['cells'] if c['stage']=='heldout']; assert len(held)==20
    primary=[];reference=[];noise=[];rows=[];direct_solved=0;rho=[]
    for rep in range(5):
        arms={c['arm']:c for c in held if c['replicate']==rep}
        aa=arms['selected-aa0'];bb=arms['selected-aa1'];ref=arms['m3-reference'];direct=arms['direct']
        for cell in (aa,bb,ref):
            r=cell['report'];assert cell['exit_code']==0 and r['status']=='solved' and cell['expected_scalar_match']
            assert r['cold_to_report_ns']>=sum(r[k] for k in ['base_construction_ns','group_preparation_ns','pair_index_ns','online_ns','extra_certificate_replay_ns'])
        assert aa['report']['certificate']==bb['report']['certificate']
        assert aa['report']['work']==bb['report']['work'] and aa['report']['base_points']==bb['report']['base_points']
        if direct['report'] is not None:
            assert aa['report']['base_points']==direct['report']['base_points']
            assert aa['report']['seed']==direct['report']['seed']
            direct_solved+=int(direct['report']['status']=='solved')
        a=aa['report']['cold_to_report_ns']/1e6;b=bb['report']['cold_to_report_ns']/1e6;r=ref['report']['cold_to_report_ns']/1e6
        primary.append(a);reference.append(r);noise.append(b/a)
        rr=next(c for c in m['cells'] if c['stage']=='rho' and c['replicate']==rep)
        assert rr['report'] and rr['report']['rho']['status']=='solved' and rr['expected_scalar_match']
        rho_ns=rr['report']['cli_accounting']['reference'];rho.append(rho_ns/1e6)
        rows.append({'replicate':rep,'selected_cold_ms':a,'aa_cold_ms':b,'m3_cold_ms':r,'selected_queries':aa['report']['work']['queries'],'selected_relations':aa['report']['work']['relations'],'selected_rank':aa['report']['work']['matrix_rank'],'memory_mib':aa['peak_rss_gib']*1024,'direct_status':direct['report']['status'] if direct['report'] else direct['status'],'direct_native_cold_ms':direct['report']['cold_to_report_ns']/1e6 if direct['report'] else None,'rho_reference_call_ms':rho_ns/1e6,'rho_search_replay_ms':rr['report']['rho']['online_wall_ns']/1e6})
    ratios=[a/b for a,b in zip(primary,reference)]
    profile=next(c['report'] for c in m['cells'] if c['stage']=='profile');assert profile['status']=='solved'
    phases=profile['phase_profile_ns'];assert phases['total']==sum(v for k,v in phases.items() if k not in ('total','clock_reads'))
    out={'schema':'m31-e2e-result/v1','standing':'pcc:unverified','selected':json.loads((HERE/'selection.json').read_text())['selected'],'primary_solved':5,'aa_solved':5,'m3_solved':5,'direct_solved':direct_solved,'rho_solved':5,'rows':rows,'median_cold_ms':statistics.median(primary),'range_cold_ms':[min(primary),max(primary)],'engineering_target_all_correct_and_median_below_1s':statistics.median(primary)<1000,'paired_selected_over_m3_geomean':geometric(ratios),'conditional_paired_bootstrap_95':interval(ratios),'aa_repeatability_ratio_range':[min(noise),max(noise)],'median_rho_reference_call_ms':statistics.median(rho),'selected_cold_over_rho_call_geomean':geometric([a/b for a,b in zip(primary,rho)]),'profile':profile,'host_qualification':'exploratory shared host; no admitted isolation or qualified speedup; bootstrap conditional on these five targets and seeds','source_commit':m['source_commit'],'evaluation_source_commit':m.get('evaluation_source_commit'),'development_nuisance':m.get('development_nuisance')}
    (HERE/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('profile','rows')},indent=2))
if __name__=='__main__':main()
