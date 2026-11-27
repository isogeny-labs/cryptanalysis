"""Validate and display recorded native output; never runs a solver."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[4]

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    manifest=json.loads((HERE/'manifest.json').read_text())
    cells=manifest['cells']
    assert len(cells)==manifest['planned_cells']==56
    assert sha(HERE/'PROTOCOL.md')==manifest['protocol_sha256']
    assert sha(HERE/'seeds.json')==manifest['seeds_sha256']
    for name,digest in manifest['inputs'].items(): assert sha(HERE/'inputs'/name)==digest
    for cell in cells:
        report=cell['native_report']
        assert report['public']['p']==2147483647
        assert report['public']['n']==2147505293
        assert report['configured_search']['summands']==cell['summands']
        assert sha(HERE/'raw'/(cell['case']+'.json'))==cell['output_sha256']
        assert cell['killed_by'] is None
    for mode in ('yield','solve'):
        for rep in (0,1):
            for m in (2,3,4):
                pair=[c for c in cells if c['mode']==mode and c['replicate']==rep and c['summands']==m and c['arm']!='interval']
                assert len(pair)==2
                assert pair[0]['input_sha256']==pair[1]['input_sha256']
                assert pair[0]['native_report']['factor_base']['columns_blake3']==pair[1]['native_report']['factor_base']['columns_blake3']
                assert pair[0]['native_report']['configured_search']['seed']==pair[1]['native_report']['configured_search']['seed']
    pdp=[c for c in cells if c['mode']=='pdp']
    assert len(pdp)==18 and all(c['native_row_replay'] for c in pdp)
    assert all(c['repeat_same_mathematical_output'] for c in pdp if c['replicate']==1)
    rho=[c for c in cells if c['mode']=='rho']
    assert all(c['rho_expected_scalar_match'] and c['native_report']['rho']['producer_check_passed'] for c in rho)
    rows=[]
    for cell in cells:
        r=cell['native_report'];w=r.get('work',{})
        rows.append({k:cell[k] for k in ('case','mode','replicate','summands','arm','wall_seconds','peak_rss_gib')} | {
            'status':r['status'],'stop_reason':r.get('stop_reason'),
            'columns':r['factor_base']['folded_columns'],
            'queries':w.get('queries'),'relations':w.get('relations'),'rank':w.get('matrix_rank'),
            'online_seconds':r.get('online_wall_seconds'),
            'preparation_seconds':r.get('target_independent_preparation_seconds'),
            'rho':r.get('rho')})
    summary={'pcc':'unverified','run':'fp-m31-local-20261127','source_commit':manifest['source_commit'],
      'flow':{'planned':56,'attempted':56,'emitted_native_report':56,'excluded':0,
        'pdp_relation_found':18,'yield_completed_prefix':10,'yield_time_censored':8,
        'ic_solve_incomplete':18,'rho_reference_solved':2},
      'status_counts':dict(Counter(c['native_status'] for c in cells)),
      'checks':{'raw_output_hashes':True,'exact_prime_field':True,'paired_public_inputs_and_seeds':True,
        'same_torus_column_hashes':True,'native_positive_row_replays':18,'identical_repeated_rows':9,
        'native_rho_scalar_replays':2,'independent_signed_replay':False},'rows':rows}
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    arms=('torus','torus-direct','interval'); colors=('#3c5aa6','#d57831','#33826d')
    fig,ax=plt.subplots(figsize=(9,3.8))
    for j,(arm,color) in enumerate(zip(arms,colors)):
        for rep,marker in ((0,'o'),(1,'x')):
            selected=[r for r in rows if r['mode']=='yield' and r['arm']==arm and r['replicate']==rep]
            ax.scatter([r['summands']+(j-1)*.15+(.025 if rep else -.025) for r in selected],
              [r['queries'] for r in selected],color=color,marker=marker,s=65,
              label=f'{arm}, target {rep}')
    ax.axhline(512,color='#666666',ls='--',lw=1,label='requested prefix (512)')
    ax.set(yscale='log',xticks=[2,3,4],xlabel='Number of summands',ylabel='Completed queries (log scale)',
      title='Native M31 relation-yield runs: completed query prefixes')
    ax.grid(axis='y',alpha=.2);ax.legend(ncol=3,fontsize=8,loc='lower left',bbox_to_anchor=(0,1.13))
    fig.text(.08,.015,'fp-m31-local-20261127 | two public targets per arm | 1.5 s soft cap | no uncertainty estimate | pcc:unverified',fontsize=8)
    fig.tight_layout(rect=[0,.045,1,.93])
    for ext in ('svg','png'):fig.savefig(HERE/('prefixes.'+ext),dpi=150)
    plt.close(fig)
    out=[]
    out += ['# Native M31 local diagnostic - 2026-11-27','',
      'The native code returned and locally replayed all 18 planted decomposition controls. None of the 18 bounded IC searches recovered an ordinary target. Two searches collected one row each (rank 1); the remaining IC searches collected none. Native Pollard rho recovered both ordinary targets and replayed their scalars. These are unsigned producer observations, not independently verified results. [pcc:unverified]','',
      'The requested coordinate field is **Fp, p=2147483647=2^31-1**. The summand counts are 2, 3, 4. Earlier binary-field/31-summand artifacts are separate and provide no evidence for this run. The native reference curve is y^2=x^3+2x+14, scalar order N=2147505293, G=(1,814455902); p and N differ. [pcc:unverified]','',
      '## Execution and evidence','',
      f"Source: `{manifest['source_commit']}`; CLI SHA256 `{manifest['binary_sha256']}`. Native fixture SHA256 `{manifest['fixture_binary_sha256']}`. Frozen protocol commit: `9846fad`; runner commit: `94c0b5d`. The protocol and seed file were committed before outcomes. The richer experiment.protocol/v1 JSON preregistration was not filed; this is a descriptive diagnostic, with no qualified A/B or speedup claim. [pcc:unverified]",'',
      'Host: AMD EPYC 9V74, shared container, five available logical CPUs; no isolation tier earned. Debug native CLI, release native fixture helper, native C rho reference. Do not compare fixture timing with solver timing. User authorized local CPU execution and local storage. Raw artifacts have not been uploaded to S3. [pcc:unverified]','',
      'Controls: 19 existing native release tests passed (3 multi_summands, 11 pipeline, 5 random_control). The helper checks [N]G=O and valid points. Solver processes receive public coordinates only; evaluator scalars stay in a separate file. The frozen factor-base child stream is reserved but unused because bases are deterministic. [pcc:unverified]','',
      'The torus and direct-torus arms use identical 71-column bases; the interval arm uses 75 columns from x=0..127. Actual paired column hashes, public input hashes and sampler seeds match. Torus uses auto/AVX2; direct arms use scalar. This is the declared arm comparison, not an isolated encoding or SIMD comparison. [pcc:unverified]','',
      'Flow: planned 56, attempted 56, native reports 56, excluded 0. PDP: 18 found rows, all locally replayed, including 9 repeated mathematical outputs. Yield: 10 complete 512-query prefixes, 8 time-censored prefixes. Solve: 18 incomplete IC searches. Rho: 2 recovered references (the enclosing one-query IC status remains incomplete). No watchdog kill or missing native report occurred. [pcc:unverified]','',
      'The CLI returns exit 1 for relation_found/incomplete in this revision. Raw exit codes are preserved; those reports are classified by native status rather than treated as process crashes. TimeBudget is checked between batches, so m4 torus exceeds its 1.5/2 s soft budget; the independent 20 s watchdog remained in force. [pcc:unverified]','',
      '## Relation-yield observations','',
      'Each row below is one target and one arm. Query counts and online seconds are native recorded values; all rows found zero relations. Only completed equal prefixes support a paired yield comparison. No timing uncertainty interval or performance ratio is asserted. [pcc:unverified]','',
      '| Target | m | Arm | Queries | Native status | Online s |','|---|---:|---|---:|---|---:|']
    for r in rows:
        if r['mode']=='yield':out.append(f"| {r['replicate']} | {r['summands']} | {r['arm']} | {r['queries']} | {r['status']} | {r['online_seconds']:.6f} |")
    out+=['','![Completed query prefixes](prefixes.svg)','','## Bounded recovery observations','',
      'IC: max_queries=65536, max_millis=2000, four walk lanes. Every run stopped incomplete. One m3 direct-torus run found 1 relation after 996 queries and one m4 direct-torus run found 1 after 24 queries, both on target 0. Both had matrix rank 1 against 71 unknown columns. This is not sufficient for recovery and does not prove that recovery is impossible. [pcc:unverified]','',
      '| Target | Rho group operations | Rho online s including local replay | Native scalar replay |','|---|---:|---:|---|']
    for r in rows:
        if r['mode']=='rho':out.append(f"| {r['replicate']} | {r['rho']['group_ops']} | {r['rho']['online_wall_seconds']:.9f} | passed |")
    out+=['',
      'The rho cap was 200000 operations. Counts exclude Rust scalar replay; online wall time includes that replay. Native CLI setup/online/reporting costs are separate in raw JSON; watcher wall time includes process lifetime. Compilation, public-fixture generation, report rendering, upstream construction and signed independent replay are outside the online interval. Complete cold cost remains unknown. IC searches did not solve, so no finite solve-time ratio to rho is reported. [pcc:unverified]','',
      '## Coverage of the original leads','',
      '| Requirement | Status in this M31 experiment | Remaining work |',
      '|---|---|---|',
      '| Target-point relations and signs | Existing public-coordinate relation search, signed planted rows and native replay exercised | Non-rational-root salvage and x(R) target-cache comparison not implemented here |',
      '| Low-degree chains and scheduling | Existing m3/m4 outer-shift plus inner-S3 split search exercised | Monolithic S4/S5, simultaneous serial/balanced systems, partial splitting and staged solver comparisons remain unimplemented in this CLI |',
      '| Explicit addition | Direct batched subtraction comparator exercised, with existing exceptional arithmetic handling | This is arithmetic search, not x,y,slope polynomial constraint solving; that encoding remains open |',
      '| Partial relations/collisions | Not run | An outside-point pool, signed coefficient elimination and generation-cost instrumentation are missing |',
      '| Factor-base constraints | Torus versus same-base direct and interval controls exercised | The binary trace constraint and Koblitz Frobenius reduction do not transfer to this prime-field experiment; broader prime-field base selection remains open |','',
      'Torus depth is membership-circuit depth, not addition-network topology. The present experiment does not discharge all five original research leads. The first next implementation comparison is a fixed-m shared-input serial/balanced/S4 system against guarded explicit addition, with a prospective protocol and equal completed prefixes. Current observed bottleneck: the existing structured m3/m4 search completes substantially shorter prefixes within its cap; test smaller flushed batches or per-query circuit work before another bounded run. Neither optimization has been measured here. [pcc:unverified]','',
      '## Reproduction and standing','',
      'The source research gate and report prose lint pass locally, and the new closed benchmark record passes its local schema/hash checks. The whole-checkout benchrec gate still reports 468 missing-artifact/report problems in historical records, with zero failures naming this new run. Remote artifact custody is unverified because this task uses authorized local storage. The PR remains a draft; no benchmark admission is inferred. [pcc:unverified]','',
      '`cargo +1.88.0 test --release --test multi_summands --test random_control --test pipeline` in `crates/prime-field-auxiliary-ic`; build `m31_public_fixture` there with `cargo +1.88.0 build --release --example m31_public_fixture`; build `ca-ic` in `suite` with `cargo +1.88.0 build --locked --bin ca-ic`. Execute `run_local.py` only in a fresh output directory; it refuses existing raw/input directories. Exact per-cell arguments, statuses, inputs and binary/source hashes are in `manifest.json`. `analyze.py` checks recorded files and renders this report. [pcc:unverified]','',
      'Local evidence: `raw/*.json`, `raw/*.txt`, `inputs/*.json`, `evaluator/scalars.json`, `manifest.json`, `summary.json`, seed/protocol files and native-control log in the delivery archive. Expected scalars are synthetic evaluator custody, never solver inputs. No new PCC IDs, execution attestation, independent signed verdict, admitted timing tier or registry promotion is supplied. [pcc:unverified]','',
      'Sources checked: native `src/circuit.rs` (direct_control and decompose_multi), `src/solve.rs` (GainGraph versus SparseSystem, row/certificate replay), `src/field.rs` (addition exceptions), `examples/cdclt_ct186_audit.rs` (reference parameters), `tests/multi_summands.rs`, `tests/pipeline.rs`, `tests/random_control.rs`, and `suite/src/cli/tools/ic/auxiliary.rs`. Research KB services were unavailable in this local checkout; source inspection is the evidence for implementation coverage. [pcc:unverified]','',
      'Canonical graph lookup: `docs/index-calculus-scoreboard.html`, `docs/ic/progress-timeline.json`, `docs/performance-gains/` and `experiments/ic-candidate-catalog/curves.yaml` are absent from this checkout; no existing prime-field auxiliary SVG was found. No qualified performance or new isogeny fact was established, so no canonical graph or leaderboard is changed. See the existing `problems/prime-field-auxiliary-ic-validation.md` for independent validation and measurement qualification. [pcc:unverified]']
    (HERE/'REPORT.md').write_text('\n'.join(out)+'\n')
    # Typst text is escaped as a JSON string, so recorded data cannot become markup.
    typ='#set page(paper: "a4", margin: 17mm, numbering: "1")\n#set text(size: 9pt)\n#set par(justify: false)\n'
    idx=0
    while idx<len(out):
        line=out[idx]
        if not line: idx+=1;continue
        if line.startswith('|'):
            table=[]
            while idx<len(out) and out[idx].startswith('|'):
                table.append([x.strip() for x in out[idx].strip('|').split('|')]);idx+=1
            columns=len(table[0]); table=table[:1]+table[2:]
            entries=', '.join('['+'#text('+json.dumps(x)+')'+']' for row in table for x in row)
            typ+=f'#table(columns: {columns}, inset: 4pt, stroke: 0.3pt + gray, {entries})\n#parbreak()\n'
            continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'))
            typ+=f'#heading(level: {level}, {json.dumps(line.lstrip("# "))})\n'
        elif line.startswith('!['):typ+='#image("prefixes.svg", width: 100%)\n#parbreak()\n'
        else:typ+=f'#text({json.dumps(line)})\n#parbreak()\n'
        idx+=1
    (HERE/'REPORT.typ').write_text(typ)
    print(json.dumps(summary['flow']))

if __name__=='__main__':main()
