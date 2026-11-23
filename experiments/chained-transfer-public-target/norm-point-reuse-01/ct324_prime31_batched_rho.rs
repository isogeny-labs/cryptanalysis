// CT324 development solver, batch-affine rho with 16 independent public-only walks.
// No optimized-rho or complete-transfer speedup claim. [pcc:unverified]
include!("ct324_batch_inverse.rs");
use std::{collections::HashMap,env,process,time::Instant};

fn prime(n:u64)->bool{
 if n<2{return false}
 if n%2==0{return n==2}
 let mut d=3;
 while d<=n/d{if n%d==0{return false}d+=2}
 true
}
fn scalar(mut k:u64,p:Point,m:u64,a:u64,c:&mut Counts)->Point{
 let mut r=None;let mut q=p;
 while k>0{
  if k&1!=0{r=baseline(r,q,m,a,c)}
  k>>=1;
  if k>0{q=baseline(q,q,m,a,c)}
 }
 r
}
fn splitmix(x:&mut u64)->u64{
 *x=x.wrapping_add(0x9e3779b97f4a7c15);
 let mut z=*x;
 z=(z^(z>>30)).wrapping_mul(0xbf58476d1ce4e5b9);
 z=(z^(z>>27)).wrapping_mul(0x94d049bb133111eb);
 z^(z>>31)
}
fn mix(x:u64)->u64{let mut t=x;splitmix(&mut t)}
fn sqrtceil(n:u64)->u64{
 let mut lo=0;let mut hi=1;
 while hi*hi<n{hi*=2}
 while lo+1<hi{let t=(lo+hi)/2;if t*t>=n{hi=t}else{lo=t}}
 hi
}
fn canonical(q:Point,a:u64,b:u64,p:u64,n:u64)->(Point,u64,u64){
 match q{
  Some(v) if v.y>p-v.y=>(Some(Pt{x:v.x,y:p-v.y}),
     if a==0{0}else{n-a},if b==0{0}else{n-b}),
  _=>(q,a,b)
 }
}
#[derive(Copy,Clone)]
struct Walker{x:Point,a:u64,b:u64,steps:u64}
fn run(args:&[String])->Result<(),String>{
 if args.len()!=9{return Err("usage: ct324-rho p a b n Gx Gy Qx Qy".into())}
 let start=Instant::now();
 let v=args[1..].iter().map(|s|s.parse::<u64>()
    .map_err(|_|"malformed public integer".to_string()))
    .collect::<Result<Vec<_>,_>>()?;
 let(p,a,b,n)=(v[0],v[1],v[2],v[3]);
 let g=Pt{x:v[4],y:v[5]};let q=Pt{x:v[6],y:v[7]};
 if p<5||p>2147483647||!prime(p)||n<3||n>4294967295||!prime(n){
  return Err("unsupported field/order".into())
 }
 if a>=p||b>=p||(4*mul(mul(a,a,p),a,p)+27*mul(b,b,p))%p==0
     ||!on(g,p,a,b)||!on(q,p,a,b){
  return Err("singular or invalid public points".into())
 }
 let mut c=Counts::default();
 if scalar(n,Some(g),p,a,&mut c).is_some()
    ||scalar(n,Some(q),p,a,&mut c).is_some(){
  return Err("public point outside specified prime subgroup".into())
 }
 let mut seed=mix(g.x^q.x.rotate_left(19)^q.y.rotate_left(31)^n);
 let salt=splitmix(&mut seed);
 let mut jumps=Vec::new();
 for _ in 0..32{
  let u=splitmix(&mut seed)%n;let v=splitmix(&mut seed)%n;
  let j=baseline(scalar(u,Some(g),p,a,&mut c),
        scalar(v,Some(q),p,a,&mut c),p,a,&mut c);
  jumps.push(if let Some(pt)=j{(Some(pt),u,v)}
             else{(Some(g),1,0)});
 }
 const LANES:usize=16;
 let mut lanes=vec![Walker{x:None,a:0,b:0,steps:0};LANES];
 let mut seen:HashMap<Point,(u64,u64)>=HashMap::new();
 let mut steps=0_u64;let mut restarts=0_u64;
 let max_steps=64*sqrtceil(n);
 while steps<max_steps{
  let take=((max_steps-steps)as usize).min(LANES);
  let mut pairs=Vec::with_capacity(take);
  for lane in lanes.iter_mut().take(take){
   if lane.steps%8192==0{
    restarts+=1;
    lane.a=splitmix(&mut seed)%n;lane.b=splitmix(&mut seed)%n;
    if lane.a==0&&lane.b==0{lane.a=1}
    lane.x=baseline(scalar(lane.a,Some(g),p,a,&mut c),
                    scalar(lane.b,Some(q),p,a,&mut c),p,a,&mut c);
   }
   let xx=lane.x.map(|pt|pt.x).unwrap_or(0);
   if n<1000||mix(xx^salt)&63==0{
    let(key,u,v)=canonical(lane.x,lane.a,lane.b,p,n);
    if let Some(&(old_u,old_v))=seen.get(&key){
     if (old_u,old_v)!=(u,v){
      // (u-old_u)G=(old_v-v)Q; check every candidate independently.
      let numerator=sub(u,old_u,n);let denominator=sub(old_v,v,n);
      if denominator!=0{
       let k=mul(numerator,pow(denominator,n-2,n),n);
       if k>0&&scalar(k,Some(g),p,a,&mut c)==Some(q){
        println!("{{\"schema\":\"ct324-native-batched-rho/v1\",\"result_scalar\":{},\"walk_steps\":{},\"distinguished_entries\":{},\"restarts\":{},\"affine_adds\":{},\"field_inversions\":{},\"batch_waves\":{},\"batched_elements\":{},\"inside_ns\":{},\"original_jacobian_calls\":0,\"pcc\":\"unverified\"}}",
          k,steps,seen.len(),restarts,c.adds,c.inversions,c.batches,
          c.elements,start.elapsed().as_nanos());
        return Ok(())
       }
      }
     }
    }else{
     if seen.len()>=65536{return Err("distinguished memory cap".into())}
     seen.insert(key,(u,v));
    }
   }
   let j=(mix(xx^salt.rotate_left(7))&31)as usize;
   let(pt,u,v)=jumps[j];
   pairs.push((lane.x,pt));
   lane.a=plus(lane.a,u,n);lane.b=plus(lane.b,v,n);lane.steps+=1;
  }
  let next=batch_add(&pairs,p,a,&mut c);
  for(lane,x)in lanes.iter_mut().zip(next){lane.x=x}
  steps+=take as u64;
 }
 Err(format!("exhausted {} walk steps, {} distinguished",steps,seen.len()))
}
fn main(){
 let args:Vec<String>=env::args().collect();
 if let Err(err)=run(&args){eprintln!("CT324 refused: {err}");process::exit(2)}
}
