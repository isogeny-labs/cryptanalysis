// CT322 bounded, cold, independently executable BSGS reference over Fp.
// No solver scalar input; unoptimized baseline, not a transferred ECDLP attack.
// All evidence and performance claims remain [pcc:unverified].
use std::collections::HashMap;
use std::env;
use std::process;
use std::time::Instant;

#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash)]
struct Point { x: u64, y: u64 }
type EPoint = Option<Point>;

#[derive(Default)]
struct Counts { adds: u64, inversions: u64 }
fn plus(x:u64,y:u64,p:u64)->u64 { (x+y)%p }
fn minus(x:u64,y:u64,p:u64)->u64 { if x>=y {x-y} else {p-(y-x)} }
fn times(x:u64,y:u64,p:u64)->u64 { (x*y)%p } // p <= 2^31-1: no u64 overflow
fn power(mut a:u64,mut e:u64,p:u64)->u64 {
    let mut v=1;
    while e>0 { if e&1!=0 {v=times(v,a,p)}; a=times(a,a,p); e>>=1; }
    v
}
fn isprime(n:u64)->bool {
    if n<2 {return false}
    if n%2==0 {return n==2}
    let mut d=3;
    while d<=n/d {if n%d==0{return false};d+=2;}
    true
}
fn on_curve(q:Point,p:u64,a:u64,b:u64)->bool {
    q.x<p && q.y<p &&
    times(q.y,q.y,p)==plus(plus(times(times(q.x,q.x,p),q.x,p),times(a,q.x,p),p),b,p)
}
fn neg(q:EPoint,p:u64)->EPoint {
    q.map(|v|Point{x:v.x,y:if v.y==0 {0} else {p-v.y}})
}
fn add(u:EPoint,v:EPoint,p:u64,a:u64,c:&mut Counts)->EPoint {
    let (r,s)=match (u,v) {(None,x)=>return x,(x,None)=>return x,(Some(x),Some(y))=>(x,y)};
    c.adds+=1;
    let (num,den)=if r.x==s.x {
        if plus(r.y,s.y,p)==0 {return None}
        (plus(times(3,times(r.x,r.x,p),p),a,p),times(2,r.y,p))
    } else {
        (minus(s.y,r.y,p),minus(s.x,r.x,p))
    };
    if den==0 {return None}
    c.inversions+=1;
    let slope=times(num,power(den,p-2,p),p);
    let x3=minus(minus(times(slope,slope,p),r.x,p),s.x,p);
    let y3=minus(times(slope,minus(r.x,x3,p),p),r.y,p);
    Some(Point{x:x3,y:y3})
}
fn scalar(mut k:u64,q:EPoint,p:u64,a:u64,c:&mut Counts)->EPoint {
    let mut r=None;
    let mut t=q;
    while k>0 {
        if k&1==1 {r=add(r,t,p,a,c)}
        k>>=1;
        if k!=0 {t=add(t,t,p,a,c)}
    }
    r
}
fn ceil_sqrt(n:u64)->u64 {
    let mut lo=0_u64;let mut hi=1_u64;
    while hi*hi<n {hi*=2}
    while lo+1<hi {
        let mid=(lo+hi)/2;
        if mid*mid>=n {hi=mid}else{lo=mid}
    }
    hi
}
fn solve(args:&[String])->Result<(),String> {
    if args.len()!=9 {return Err("usage: ct322-bsgs p a b n Gx Gy Qx Qy (public only)".into())}
    let t0=Instant::now();
    let vv=args[1..].iter().map(|s|s.parse::<u64>().map_err(|_|"invalid unsigned integer".to_string())).collect::<Result<Vec<_>,_>>()?;
    let (p,a,b,n)=(vv[0],vv[1],vv[2],vv[3]);
    let (g,q)=(Point{x:vv[4],y:vv[5]},Point{x:vv[6],y:vv[7]});
    if p<5 || p>2147483647 || n<3 || n>4294967295 || !isprime(p) || !isprime(n) {
        return Err("prime p/n outside bounded domain".into());
    }
    if a>=p || b>=p || (4*times(times(a,a,p),a,p)+27*times(b,b,p))%p==0 {
        return Err("noncanonical or singular curve".into());
    }
    if !on_curve(g,p,a,b) || !on_curve(q,p,a,b) {
        return Err("G or Q noncanonical/off curve".into());
    }
    let mut counts=Counts::default();
    if scalar(n,Some(g),p,a,&mut counts).is_some() ||
       scalar(n,Some(q),p,a,&mut counts).is_some() {
        return Err("G or Q is not in prime subgroup".into());
    }
    let m=ceil_sqrt(n);
    if m>65536 {return Err("baby-table cap exceeded".into())}
    let mut babies:HashMap<EPoint,u64>=HashMap::with_capacity(m as usize);
    let mut r=None;
    for j in 0..m {
        babies.entry(r).or_insert(j);
        r=add(r,Some(g),p,a,&mut counts);
    }
    let step=neg(scalar(m,Some(g),p,a,&mut counts),p);
    let mut gamma=Some(q);
    let mut found=None;
    let mut giants=0u64;
    for i in 0..=(n/m+1) {
        giants+=1;
        if let Some(&j)=babies.get(&gamma) {
            let k=(i*m+j)%n;
            if k>=1 && scalar(k,Some(g),p,a,&mut counts)==Some(q) {
                found=Some(k);break
            }
        }
        gamma=add(gamma,step,p,a,&mut counts);
    }
    let k=found.ok_or("BSGS failed to recover the source subgroup DLP")?;
    let elapsed=t0.elapsed().as_nanos();
    println!("{{\"schema\":\"ct322-native-bsgs/v1\",\"result_scalar\":{},\"baby_table_entries\":{},\"baby_iterations\":{},\"giant_iterations\":{},\"affine_adds\":{},\"field_inversions\":{},\"inside_ns\":{},\"original_jacobian_calls\":0,\"pcc\":\"unverified\"}}",
        k,babies.len(),m,giants,counts.adds,counts.inversions,elapsed);
    Ok(())
}
fn main() {
    let a:Vec<String>=env::args().collect();
    if let Err(e)=solve(&a) {eprintln!("CT322 refused: {}",e);process::exit(2)}
}
