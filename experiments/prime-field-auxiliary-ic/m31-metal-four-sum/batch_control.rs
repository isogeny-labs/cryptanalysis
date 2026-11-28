use prime_field_auxiliary_ic::{Config, Curve, FactorBase, MultiSolveOutcome, PairIndex, PreparedSolver};

fn main() {
    let c=Curve::<31>::new(2,14).unwrap();
    let g=c.point(1,814455902).unwrap();
    let q=c.point(1767503692,244402461).unwrap();
    let roots:Vec<_>=(0..c.modulus()).filter(|&x| c.lift_x(x).unwrap().is_some()).take(195).collect();
    let base=FactorBase::without_maps(c,&roots).unwrap();
    let prepared=PreparedSolver::new(&base,2_147_505_293,g).unwrap();
    let index=PairIndex::new(&base,4_194_304,16_384).unwrap();
    let config=Config { seed:2_911_332_506_172_719_186, max_queries:100_000, walk_lanes:64, ..Config::default() };
    let (serial,_)=prepared.solve_multi_indexed(4,q,&config,&index).unwrap();
    let (batch,_)=prepared.solve_multi_indexed_batched(4,q,&config,&index).unwrap();
    assert_eq!(serial,batch,"lane-batch adapter changed the certificate or work trace");
    match batch {
        MultiSolveOutcome::Solved { certificate,stats } => println!("{{\"equal\":true,\"scalar\":{},\"queries\":{},\"relations\":{},\"rank\":{}}}",certificate.scalar,stats.queries,stats.relations,stats.matrix_rank),
        MultiSolveOutcome::Exhausted { reason,.. } => panic!("unexpected exhaustion: {reason:?}"),
    }
}
