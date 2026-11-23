// CT323: bounded public-only affine Pollard rho with negation-class
// distinguished-point collision detection. A control, not best optimized rho.
// Source/cost evidence [pcc:unverified].
use std::collections::HashMap;
use std::env;
use std::process;
use std::time::Instant;

#[derive(Copy,Clone,Debug,Eq,PartialEq,Hash)]
struct Pt { x:u64, y:u64 }
type Point=Option<Pt>;
#[derive(Default)]
struct C { add:u64, inv:u64 }
fn plus(a:u64,b:u64,m:u64)->u64{(a+b)%m}
fn sub(a:u64,b:u64,m:u64)->u64{if a>=b{a-b}else{m-(b-a)}}
fn mul(a:u64,b:u64,m:u64)->u64{a*b%m}
fn pow(mut a:u64,mut n:u64,m:u64)->u64{
    let mut r=1;
    while n>0 {if n&1!=0 {r=mul(r,a,m)} a=mul(a,a,m);n>>=1;}
    r
}
fn prime(n:u64)->bool{
    if n<2{return false}
    if n%2==0{return n==2}
    let mut d=3;
    while d<=n/d {if n%d==0{return false}d+=2;}
    true
}
fn on(p:Pt,m:u64,a:u64,b:u64)->bool{
    p.x<m && p.y<m &&
    mul(p.y,p.y,m)==plus(plus(mul(mul(p.x,p.x,m),p.x,m),mul(a,p.x,m),m),b,m)
}
fn add(x:Point,y:Point,m:u64,a:u64,c:&mut C)->Point{
    let (u,v)=match (x,y) {(None,q)=>return q,(q,None)=>return q,(Some(u),Some(v))=>(u,v)};
    c.add+=1;
    let (num,den)=if u.x==v.x {
        if plus(u.y,v.y,m)==0{return None}
        (plus(mul(3,mul(u.x,u.x,m),m),a,m),mul(2,u.y,m))
    }else{(sub(v.y,u.y,m),sub(v.x,u.x,m))};
    if den==0{return None}
    c.inv+=1;
    let s=mul(num,pow(den,m-2,m),m);
    let x3=sub(sub(mul(s,s,m),u.x,m),v.x,m);
    let y3=sub(mul(s,sub(u.x,x3,m),m),u.y,m);
    Some(Pt{x:x3,y:y3})
}
fn scalar(mut k:u64,p:Point,m:u64,a:u64,c:&mut C)->Point{
    let mut r=None;let mut q=p;
    while k>0 {
        if k&1!=0{r=add(r,q,m,a,c)}
        k>>=1;
        if k>0{q=add(q,q,m,a,c)}
    }
    r
}
fn csqrt(n:u64)->u64{
    let mut a=0;let mut b=1;
    while b*b<n {b*=2;}
    while a+1<b {
        let x=(a+b)/2;
        if x*x>=n{b=x}else{a=x}
    }
    b
}
fn splitmix(x:&mut u64)->u64 {
    *x=x.wrapping_add(0x9e3779b97f4a7c15);
    let mut z=*x;
    z=(z^(z>>30)).wrapping_mul(0xbf58476d1ce4e5b9);
    z=(z^(z>>27)).wrapping_mul(0x94d049bb133111eb);
    z^(z>>31)
}
fn mix(x:u64)->u64 {let mut t=x;splitmix(&mut t)}
fn canonical(q:Point,a:u64,b:u64,p:u64,n:u64)->(Point,u64,u64) {
    match q {
        Some(v) if v.y>p-v.y => (Some(Pt{x:v.x,y:p-v.y}),
                                    if a==0{0}else{n-a},
                                    if b==0{0}else{n-b}),
        _ => (q,a,b)
    }
}
fn run(args:&[String])->Result<(),String>{
    if args.len()!=9{return Err("usage: ct323-rho p a b n Gx Gy Qx Qy (public only)".into())}
    let start=Instant::now();
    let vs=args[1..].iter().map(|x|x.parse::<u64>()
        .map_err(|_|"malformed public integer".to_string()))
        .collect::<Result<Vec<_>,_>>()?;
    let (p,a,b,n)=(vs[0],vs[1],vs[2],vs[3]);
    let g=Pt{x:vs[4],y:vs[5]};let q=Pt{x:vs[6],y:vs[7]};
    if p<5 || p>2147483647 || !prime(p) || n<3 || n>4294967295 || !prime(n) {
        return Err("outside bounded prime field/order".into());
    }
    if a>=p || b>=p || (4*mul(mul(a,a,p),a,p)+27*mul(b,b,p))%p==0 {
        return Err("singular/noncanonical coefficients".into());
    }
    if !on(g,p,a,b) || !on(q,p,a,b){return Err("off-curve public point".into())}
    let mut c=C::default();
    if scalar(n,Some(g),p,a,&mut c).is_some() ||
       scalar(n,Some(q),p,a,&mut c).is_some(){
        return Err("point not in prime subgroup".into());
    }
    let m=csqrt(n);
    let max_steps=64*m;
    let mut seed=mix(g.x^q.x.rotate_left(19)^q.y.rotate_left(31)^n);
    let salt=splitmix(&mut seed);
    let mut jump:Vec<(Point,u64,u64)>=Vec::new();
    for _ in 0..32 {
        let u=splitmix(&mut seed)%n;
        let v=splitmix(&mut seed)%n;
        let mut j=add(scalar(u,Some(g),p,a,&mut c),
                      scalar(v,Some(q),p,a,&mut c),p,a,&mut c);
        let (mut uu,mut vv)=(u,v);
        if j.is_none(){j=Some(g);uu=1;vv=0}
        jump.push((j,uu,vv));
    }
    let mut seen:HashMap<Point,(u64,u64)>=HashMap::new();
    let mut steps=0_u64;
    let mut restarts=0_u64;
    let mut x=None;let mut aa=0;let mut bb=0;
    while steps<max_steps {
        if steps%8192==0 {
            restarts+=1;
            aa=splitmix(&mut seed)%n;
            bb=splitmix(&mut seed)%n;
            if aa==0 && bb==0 {aa=1}
            x=add(scalar(aa,Some(g),p,a,&mut c),
                  scalar(bb,Some(q),p,a,&mut c),p,a,&mut c);
        }
        // The raw walk does NOT canonicalize each step: this avoids the
        // systematic 2-cycle of naive negation-quotient additive walks.
        // Only stored distinguished points use signed canonicalization.
        let xx=x.map(|v|v.x).unwrap_or(0);
        if n<1000 || mix(xx^salt)&15==0 {
            let (key,u,v)=canonical(x,aa,bb,p,n);
            if let Some(&(old_u,old_v))=seen.get(&key) {
                if (old_u,old_v)!=(u,v) {
                    // (u-old_u)G = (old_v-v)Q.
                    let num=sub(u,old_u,n);
                    let den=sub(old_v,v,n);
                    if den!=0 {
                        let log=mul(num,pow(den,n-2,n),n);
                        if log>0 && scalar(log,Some(g),p,a,&mut c)==Some(q) {
                            println!("{{\"schema\":\"ct323-native-rho/v1\",\"result_scalar\":{},\"walk_steps\":{},\"distinguished_entries\":{},\"restarts\":{},\"affine_adds\":{},\"field_inversions\":{},\"inside_ns\":{},\"original_jacobian_calls\":0,\"pcc\":\"unverified\"}}",
                                log,steps,seen.len(),restarts,c.add,c.inv,start.elapsed().as_nanos());
                            return Ok(())
                        }
                    }
                }
            }else{
                if seen.len()>=65536 {
                    return Err("distinguished-entry memory cap".into());
                }
                seen.insert(key,(u,v));
            }
        }
        let j=(mix(xx^salt.rotate_left(7))&31)as usize;
        let (pt,u,v)=jump[j];
        x=add(x,pt,p,a,&mut c);
        aa=plus(aa,u,n);
        bb=plus(bb,v,n);
        steps+=1;
    }
    Err(format!("bounded rho did not solve: steps={}, restarts={}, entries={}",
                steps,restarts,seen.len()))
}
fn main(){
    let args:Vec<String>=env::args().collect();
    if let Err(err)=run(&args){eprintln!("CT323 refused: {}",err);process::exit(2);}
}
