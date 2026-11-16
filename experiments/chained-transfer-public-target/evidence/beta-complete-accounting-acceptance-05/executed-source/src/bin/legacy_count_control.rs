//! Actual legacy accounting claim rejection, under prospective protocol02.
use chained_n4_beta_complete_evaluator::complete::CompleteBeta;
use chained_n4_public_target::CheckedInstance;
fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 2);
    assert_eq!(args[1], "--legacy-32-isogenies");
    let c = CheckedInstance::construct().unwrap();
    let b = CompleteBeta::construct(&c).unwrap();
    eprintln!(
        "ACTUAL_CONSTRUCTOR_CALLS {}",
        serde_json::to_string(b.preprocessing_calls()).unwrap()
    );
    let actual: u64 = b
        .preprocessing_calls()
        .torsion_source_isogeny_evaluations
        .iter()
        .sum();
    assert_eq!(actual, 32, "the historical32-count metadata is false; real constructor calls are counted at executed sites");
}
