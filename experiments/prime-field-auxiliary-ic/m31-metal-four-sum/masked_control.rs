use prime_field_auxiliary_ic::{Curve,FactorBase,PairIndex};
use std::time::Instant;

fn main() {
    let args:Vec<_>=std::env::args().collect();
    let c=Curve::<31>::new(2,14).unwrap();
    let roots:Vec<_>=(0..c.modulus()).filter(|&x| c.lift_x(x).unwrap().is_some()).take(195).collect();
    let base=FactorBase::without_maps(c,&roots).unwrap();
    let index=PairIndex::new(&base,4_194_304,16_384).unwrap();
    assert_eq!(index.stats().entries,38_025);
    let targets:Vec<_>=std::fs::read_to_string(&args[1]).unwrap().lines().map(|line| {
        let (x,y)=line.split_once(',').unwrap();
        c.point(x.parse().unwrap(),y.parse().unwrap()).unwrap()
    }).collect();
    let flags=std::fs::read(&args[2]).unwrap();
    let width=2*index.stats().entries;
    assert_eq!(flags.len(),targets.len()*width);
    let mut ordinary=index.workspace();
    let mut masked=index.workspace();
    let start=Instant::now();
    let expected:Vec<_>=targets.iter().map(|&point| index.decompose(4,point,&mut ordinary).unwrap()).collect();
    let ordinary_ns=start.elapsed().as_nanos();
    let start=Instant::now();
    let found:Vec<_>=targets.iter().enumerate().map(|(i,&point)| index.decompose_masked(point,&mut masked,&flags[i*width..(i+1)*width]).unwrap()).collect();
    let masked_ns=start.elapsed().as_nanos();
    assert_eq!(expected,found,"GPU-screened first witnesses differ");
    println!("{{\"targets\":{},\"equal\":true,\"hits\":{},\"ordinary_ns\":{ordinary_ns},\"masked_ns\":{masked_ns},\"ordinary_lookups\":{},\"masked_lookups\":{}}}",targets.len(),found.iter().filter(|x|x.is_some()).count(),ordinary.stats().lookups,masked.stats().lookups);
}
