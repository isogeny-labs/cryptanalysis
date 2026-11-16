"""Adapt the complete accepted sampler harness using literal source substitutions."""
from pathlib import Path
import json,shutil
s=Path('/workspace/cryptanalysis/experiments/chained-transfer-public-target');p=s/'original-fixed-model-sampler-01';old=(s/'norm-assisted-ic/src/tests.rs').read_text();base=(s/'original-fixed-model-ic-01/src/tests.rs').read_text()
header='''use super::*;
use chained_n4_completed_v2::AdapterV2;
use chained_n4_original_fixed_model_ic::{class_solver as baseline, TargetContext};
use chained_n4_original_full_evaluator::Runtime;
use chained_n4_original_full_geometry::{Adapter, take_fixed_model, CASES};
use chained_n4_paired_fourth_preflight::{models::{construct_all, SourceE}, PairedFourth, ThirdHop, TwistedPair};
use chained_n4_public_target::{ghs::EP, CheckedInstance};
use isogeny_algos::fpr::ER;
use serde_json::{json, Value};

'''
point_helpers=base[base.index('fn short('):base.index('fn parameters(')]
comparison_helpers=old[old.index('macro_rules! report'):old.index('#[test]')]
t=old[old.index('#[test]'):];changes=[]
def once(a,b):
 global t
 assert t.count(a)==1,(a,t.count(a));t=t.replace(a,b,1);changes.append(dict(old=a,new=b))
once('fn exact_scalar_samples_and_all_sixty_original_candidate_ic_pairs()', 'fn all_original_fixed_models_all_scalar_triples_and_sixty_paired_attempts()')
once('"protocol":"4a6745/b57 published beforecode"','"protocol":"abf432/80631ad before new Rust"')
a=t.index('    let c = CheckedInstance::construct().unwrap();');b=t.index('    let public =',a)
replacement='''    let c = CheckedInstance::construct().unwrap();
    let old = AdapterV2::new(&c).unwrap();
    let runtime = Runtime::construct(&c).unwrap();
    let pair = ThirdHop::construct(&c);
    let twisted_pair = TwistedPair::construct(&c);
    let fourth = PairedFourth::construct(&c, &twisted_pair);
    let known_generator_points = source_points(&c, &pair, &fourth, c.inst.g);
    let generators = packets(&runtime, known_generator_points);
'''
changes.append(dict(old=t[a:b],new=replacement));t=t[:a]+replacement+t[b:]
marker='    let (mut pairs, mut scalar_pairs, mut triples, mut solved_cases, mut models_seen) ='
once(marker,'''    let public_packets: Vec<_> = public.iter().map(|&q|packets(&runtime, source_points(&c, &pair, &fourth, q))).collect();
    println!("N4_ORIGINAL_FIXED_SAMPLER_SETUP {}",json!({"whole_original_runtime_setup":runtime.setup,"actual_input_transfer_calls":runtime.calls(),"scope":"complete original setup retained, not minimal or priced"}));
'''+marker)
a=t.index('    for model in models {');b=t.index('        let preparation = prepared.calls();',a)
replacement='''    for side in 0..3 {
        let model = &runtime.geometry.models[side];
        let source = &model.source;
        let id = [CASES[side].0, CASES[side].1];
        let norm = &model.prime;
        let g = generators[side].clone();
        let gc = norm.decode(&g).unwrap();
        let prepared = SamplerContext::new(&runtime.geometry, side, &g).unwrap();
        let baseline_context = TargetContext::new(&runtime.geometry, side).unwrap();
        let pic = &norm.a.pic;
        assert_eq!(prepared.prepared_source(), kp(known_generator_points[side]), "public norm preparation differs from independently transported known generator point");
'''
changes.append(dict(old=t[a:b],new=replacement));t=t[:a]+replacement+t[b:]
once('''        for &raw in &public {
            let q = chain
                .from_source(&chain.encode_source(short(&c, raw)))
                .unwrap();''','''        for (public_index, _) in public.iter().enumerate() {
            let q = public_packets[public_index][side].clone();''')
once('"prepared_public_source":prepared.prepared_source(),','"prepared_public_source":prepared.prepared_source(),"independent_already_known_source_point":kp(known_generator_points[side]),"strong_known_point_reference_exact":true,')
t=t.replace('SamplerContext::new(&norm,','SamplerContext::new(&runtime.geometry, side,')
once('    let mut foreign: Option<EncodedClass> = None;\n','')
a=t.index('        if let Some(ref bad) = foreign {');b=t.index('        // Same quartic',a)
replacement='''        let bad = &generators[(side+1)%3];
        assert!(SamplerContext::new(&runtime.geometry, side, bad).is_err());
        assert!(prepared.solve(bad, &g, &candidate_params(36), 103).is_err());
        assert!(prepared.solve(&g, bad, &candidate_params(36), 103).is_err());
        controls.push("actual-foreign-Jacobian-and-P0");
        assert!(SamplerContext::new(&runtime.geometry, 3, &g).is_err());
        controls.push("invalid-fixed-side");
        for kind in 0..5 {
            let mut bad = candidate_params(36);
            match kind { 0=>bad.nfb=3, 1=>bad.nfb=225, 2=>bad.max_desc=0, 3=>bad.rows_mult=f64::NAN, 4=>bad.rows_mult=0.0, _=>unreachable!() }
            assert!(prepared.solve(&g,&g,&bad,103).is_err());
        }
        controls.push("five-invalid-bounded-parameters");
'''
changes.append(dict(old=t[a:b],new=replacement));t=t[:a]+replacement+t[b:]
a=t.index('        let (alternate_models, _) = construct_all(');b=t.index('        let alternate_norm =',a)
replacement='''        let (mut alternate_models, _) = construct_all(source, &old);
        let alternate_model = take_fixed_model(&mut alternate_models, side, chained_n4_original_full_geometry::MASKS[side]).unwrap();
'''
changes.append(dict(old=t[a:b],new=replacement));t=t[:a]+replacement+t[b:]
once('Adapter::with_base_point(&source, &old.a, alternate_model, Some(alternate))','Adapter::with_base_point(source, &old, alternate_model, Some(alternate))')
once('        foreign = Some(g.clone());\n','')
t=t.replace('N4_NORM_SAMPLER_','N4_ORIGINAL_FIXED_SAMPLER_').replace('"target":id,','"side":side,"target":id,')
(p/'src/tests.rs').write_text(header+point_helpers+comparison_helpers+t)
(p/'test-source-provenance.json').write_text(json.dumps(dict(original_harness='norm-assisted-ic/src/tests.rs',accepted_point_helpers='original-fixed-model-ic-01/src/tests.rs',comparison_report_and_parameter_helpers_literal=True,exact_substitutions=changes,additional_controls='allthree actual cross-target packets, exact fixed side/params, independently transported known initial point equality',all_old75_scalar_list_rng_and225_1125_60_120_15_criteria_unchanged=True,no_scalar_answers_in_solver_context=True),indent=2)+'\n');shutil.copyfile(__file__,p/'materialize-test.py')
print('complete old sampler harness adapted; source point helpers and comparisons literal',flush=True)
