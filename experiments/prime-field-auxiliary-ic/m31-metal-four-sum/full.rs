use prime_field_auxiliary_ic::{verify_multi_certificate,Config,Curve,Error,FactorBase,MultiSolveOutcome,PairIndex,PreparedSolver};
use std::{ffi::CString,time::{Instant,Duration}};

#[repr(C)]
#[derive(Clone,Copy)]
struct WirePoint { x:u64, y:u64, finite:u64 }
#[link(name="m31metal")]
unsafe extern "C" {
    fn m31_metal_init(points:*const WirePoint,count:i32,bits:*const u64,words:i32,bitmap_bits:i32,use_coarse:i32,path:*const i8)->i32;
    fn m31_metal_screen(targets:*const WirePoint,count:i32,output:*mut u8)->i32;
}
fn wire(point:Option<prime_field_auxiliary_ic::Point>)->WirePoint {
    point.map_or(WirePoint{x:0,y:0,finite:0},|p| WirePoint{x:p.x(),y:p.y(),finite:1})
}
fn main() {
    let args:Vec<_>=std::env::args().collect();
    let mode=args.get(1).expect("cpu or metal").as_str();
    assert!(mode=="cpu" || mode=="metal");
    let started=Instant::now();
    let c=Curve::<31>::new(2,14).unwrap();
    let g=c.point(1,814455902).unwrap();
    let qx=args.get(2).map_or(1_767_503_692,|x|x.parse().unwrap());
    let qy=args.get(3).map_or(244_402_461,|x|x.parse().unwrap());
    let seed=args.get(4).map_or(2_911_332_506_172_719_186,|x|x.parse().unwrap());
    let bitmap_bits:usize=args.get(5).map_or(20,|x|x.parse().unwrap());
    let use_coarse:i32=args.get(6).map_or(0,|x|x.parse().unwrap());
    assert!(bitmap_bits==20 || bitmap_bits==22);
    assert!(use_coarse==0 || ((use_coarse==1 || use_coarse==2) && bitmap_bits==22));
    let q=c.point(qx,qy).unwrap();
    let roots:Vec<_>=(0..c.modulus()).filter(|&x| c.lift_x(x).unwrap().is_some()).take(195).collect();
    let base=FactorBase::without_maps(c,&roots).unwrap();
    let prepared=PreparedSolver::new(&base,2_147_505_293,g).unwrap();
    let index=PairIndex::new_with_bitmap_bits(&base,4_194_304,16_384,bitmap_bits).unwrap();
    let setup_ns=started.elapsed().as_nanos();
    let config=Config { seed,max_queries:100_000,walk_lanes:64,
        max_duration:Some(Duration::from_secs(5)),..Config::default() };
    let mut metal_init_ns=0;
    let mut screens=0u64;
    let mut screen_ns=0u128;
    let mut positive_flags=0u64;
    let audit_flags=std::env::var_os("M31_AUDIT_FLAGS").is_some();
    let mut flag_digest=14_695_981_039_346_656_037u64;
    let online=Instant::now();
    let (outcome,probe)=if mode=="cpu" {
        prepared.solve_multi_indexed(4,q,&config,&index).unwrap()
    } else {
        let screen_points=index.screen_points();
        let entries:Vec<_>=screen_points.iter().copied().map(wire).collect();
        let bitmap=index.screen_bitmap();
        assert_eq!(bitmap.len(),1 << (bitmap_bits-6));
        let path=std::env::current_dir().unwrap().join("experiments/prime-field-auxiliary-ic/m31-metal-four-sum/screen.metal");
        let path=CString::new(path.to_str().unwrap()).unwrap();
        let init=Instant::now();
        let code=unsafe { m31_metal_init(entries.as_ptr(),entries.len() as i32,bitmap.as_ptr(),bitmap.len() as i32,bitmap_bits as i32,use_coarse,path.as_ptr()) };
        assert_eq!(code,0,"Metal initialization failed");
        metal_init_ns=init.elapsed().as_nanos();
        prepared.solve_multi_indexed_screened(q,&config,&index,|points| {
            let targets:Vec<_>=points.iter().copied().map(wire).collect();
            let mut flags=vec![0u8;targets.len()*entries.len()*2];
            let screen_started=Instant::now();
            let code=unsafe { m31_metal_screen(targets.as_ptr(),targets.len() as i32,flags.as_mut_ptr()) };
            screen_ns+=screen_started.elapsed().as_nanos();
            if code!=0 { return Err(Error::Invalid("Metal candidate dispatch")); }
            if std::env::var_os("M31_AUDIT_EXACT_X").is_some() && screens==0 && use_coarse==2 {
                let present:std::collections::HashSet<_>=screen_points.iter().flatten().map(|p|p.x()).collect();
                for (i,&outer) in screen_points.iter().enumerate() {
                    for sign in 0..2 {
                        let term=if sign==0 { outer.map(|p|c.negate(p)).transpose()? } else {outer};
                        let candidate=c.add(points[0],term)?;
                        let expected=match candidate {
                            None=>2,
                            Some(p)=>u8::from(present.contains(&p.x())),
                        };
                        assert_eq!(flags[2*i+sign],expected,"first-round exact x flag {i}/{sign}");
                    }
                }
            }
            if audit_flags {
                for &flag in &flags { flag_digest=(flag_digest^u64::from(flag)).wrapping_mul(1_099_511_628_211); }
            }
            screens+=1;
            positive_flags+=flags.iter().filter(|&&x|x!=0).count() as u64;
            Ok(flags)
        }).unwrap()
    };
    let online_ns=online.elapsed().as_nanos();
    let MultiSolveOutcome::Solved { certificate,stats }=outcome else { panic!("bounded solve incomplete: {outcome:?}") };
    verify_multi_certificate(&base,&certificate).unwrap();
    assert_eq!(c.mul(Some(g),certificate.scalar).unwrap(),Some(q));
    let mut digest=14_695_981_039_346_656_037u64;
    for word in [certificate.summands as u64,certificate.order,
                 certificate.generator.x(),certificate.generator.y(),
                 certificate.target.x(),certificate.target.y(),certificate.scalar,
                 certificate.relations.len() as u64,certificate.weights.len() as u64] {
        digest=(digest^word).wrapping_mul(1_099_511_628_211);
    }
    for row in &certificate.relations {
        for word in [row.a,row.b] { digest=(digest^word).wrapping_mul(1_099_511_628_211); }
        digest=(digest^(row.decomposition.summands().len() as u64)).wrapping_mul(1_099_511_628_211);
        for term in row.decomposition.summands() {
            digest=(digest^(term.index as u64)).wrapping_mul(1_099_511_628_211);
            digest=(digest^u64::from(term.negative)).wrapping_mul(1_099_511_628_211);
        }
    }
    for &weight in &certificate.weights {
        digest=(digest^weight).wrapping_mul(1_099_511_628_211);
    }
    let total_ns=started.elapsed().as_nanos();
    println!("{{\"schema\":\"m31-metal-full-rust/v2\",\"mode\":\"{mode}\",\"bitmap_bits\":{bitmap_bits},\"use_coarse\":{use_coarse},\"Q\":[{qx},{qy}],\"seed\":{seed},\"status\":\"solved\",\"scalar\":{},\"certificate_digest\":{digest},\"flag_digest\":{flag_digest},\"queries\":{},\"relations\":{},\"rank\":{},\"generated_candidates\":{},\"lookups\":{},\"gpu_screens\":{screens},\"screen_ns\":{screen_ns},\"positive_flags\":{positive_flags},\"setup_ns\":{setup_ns},\"metal_init_ns\":{metal_init_ns},\"online_ns\":{online_ns},\"total_ns\":{total_ns}}}",certificate.scalar,stats.queries,stats.relations,stats.matrix_rank,probe.generated_candidates,probe.lookups);
}
