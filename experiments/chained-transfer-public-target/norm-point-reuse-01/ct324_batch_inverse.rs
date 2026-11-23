// CT324: batched affine group-addition kernel, no complete-solver timing claim.
// p <= 2^31-1, with canonical points on short Weierstrass curves.
#[derive(Copy,Clone,Debug,PartialEq,Eq)]
struct Pt{x:u64,y:u64}
type Point=Option<Pt>;
#[derive(Default,Debug)]struct Counts{adds:u64,inversions:u64,batches:u64,elements:u64}
fn plus(a:u64,b:u64,p:u64)->u64{(a+b)%p}
fn sub(a:u64,b:u64,p:u64)->u64{if a>=b{a-b}else{p-(b-a)}}
fn mul(a:u64,b:u64,p:u64)->u64{a*b%p}
fn pow(mut a:u64,mut e:u64,p:u64)->u64{
 let mut r=1;while e!=0{if e&1!=0{r=mul(r,a,p)}a=mul(a,a,p);e>>=1;}r
}
fn on(v:Pt,p:u64,a:u64,b:u64)->bool{
 v.x<p&&v.y<p&&mul(v.y,v.y,p)==plus(plus(mul(mul(v.x,v.x,p),v.x,p),mul(a,v.x,p),p),b,p)
}
fn baseline(q:Point,r:Point,p:u64,a:u64,c:&mut Counts)->Point{
 let (u,v)=match(q,r){(None,t)|(t,None)=>return t,(Some(u),Some(v))=>(u,v)};
 c.adds+=1;
 let (num,den)=if u.x==v.x{
  if plus(u.y,v.y,p)==0{return None}
  (plus(mul(3,mul(u.x,u.x,p),p),a,p),mul(2,u.y,p))
 }else{(sub(v.y,u.y,p),sub(v.x,u.x,p))};
 if den==0{return None}
 c.inversions+=1;
 let slope=mul(num,pow(den,p-2,p),p);
 let x=sub(sub(mul(slope,slope,p),u.x,p),v.x,p);
 let y=sub(mul(slope,sub(u.x,x,p),p),u.y,p);
 Some(Pt{x,y})
}
fn batch_add(pairs:&[(Point,Point)],p:u64,a:u64,c:&mut Counts)->Vec<Point>{
 let mut out=vec![None;pairs.len()];
 let mut jobs:Vec<(usize,Pt,Pt,u64,u64)>=Vec::new();
 for (idx,&(q,r)) in pairs.iter().enumerate(){
  let (u,v)=match(q,r){(None,t)|(t,None)=>{out[idx]=t;continue},(Some(u),Some(v))=>(u,v)};
  c.adds+=1;
  let (num,den)=if u.x==v.x{
   if plus(u.y,v.y,p)==0{continue}
   (plus(mul(3,mul(u.x,u.x,p),p),a,p),mul(2,u.y,p))
  }else{(sub(v.y,u.y,p),sub(v.x,u.x,p))};
  if den!=0{jobs.push((idx,u,v,num,den))}
 }
 if jobs.is_empty(){return out}
 c.batches+=1;c.elements+=jobs.len() as u64;
 let mut prefixes=Vec::with_capacity(jobs.len());
 let mut product=1;
 for &(_,_,_,_,den) in &jobs{
  prefixes.push(product);product=mul(product,den,p);
 }
 let mut inverted=pow(product,p-2,p);c.inversions+=1;
 for j in (0..jobs.len()).rev(){
  let (idx,u,v,num,den)=jobs[j];
  let inv=mul(inverted,prefixes[j],p);
  inverted=mul(inverted,den,p);
  let slope=mul(num,inv,p);
  let x=sub(sub(mul(slope,slope,p),u.x,p),v.x,p);
  let y=sub(mul(slope,sub(u.x,x,p),p),u.y,p);
  out[idx]=Some(Pt{x,y});
 }
 out
}
#[cfg(test)]mod tests{
 use super::*;
 fn multiples(g:Point,k:usize,p:u64,a:u64)->Vec<Point>{
  let mut v=vec![None];let mut c=Counts::default();
  for _ in 0..k{v.push(baseline(*v.last().unwrap(),g,p,a,&mut c))}
  v
 }
 fn compare(points:&[Point],p:u64,a:u64)->(Counts,Counts){
  let pairs=points.iter().flat_map(|&u|points.iter().map(move |&v|(u,v))).collect::<Vec<_>>();
  let mut bat=Counts::default();let mut ind=Counts::default();
  let out=batch_add(&pairs,p,a,&mut bat);
  let expected=pairs.iter().map(|&(u,v)|baseline(u,v,p,a,&mut ind)).collect::<Vec<_>>();
  assert_eq!(out,expected);(bat,ind)
 }
 #[test]fn toy_all_25_pairs(){
  let p=97;let a=2;let b=3;let g=Some(Pt{x:3,y:6});
  let points=multiples(g,4,p,a);
  assert!(points.iter().flatten().all(|&q|on(q,p,a,b)));
  let (bat,ind)=compare(&points,p,a);
  assert_eq!(bat.inversions,1);assert!(ind.inversions>bat.inversions);
 }
 #[test]fn prime31_256_pairs(){
  let p=2147483647;let a=847514846;let b=2087444724;
  let g=Some(Pt{x:625037715,y:2100627251});
  assert!(on(g.unwrap(),p,a,b));
  let points=multiples(g,15,p,a);
  assert!(points.iter().flatten().all(|&q|on(q,p,a,b)));
  let (bat,ind)=compare(&points,p,a);
  assert_eq!(bat.inversions,1);assert!(ind.inversions>bat.inversions);
 }
 #[test]fn all_infinity_has_zero_inverse(){
  let mut c=Counts::default();
  assert_eq!(batch_add(&[(None,None),(None,None)],97,2,&mut c),vec![None,None]);
  assert_eq!(c.inversions,0);assert_eq!(c.batches,0);
 }
 #[test]fn vertical_and_identity(){
  let p=97;let g=Some(Pt{x:3,y:6});let neg=Some(Pt{x:3,y:91});
  let pairs=[(g,neg),(g,None),(None,g),(g,g)];
  let mut bat=Counts::default();let mut ind=Counts::default();
  assert_eq!(batch_add(&pairs,p,2,&mut bat),
             pairs.iter().map(|&(u,v)|baseline(u,v,p,2,&mut ind)).collect::<Vec<_>>());
  assert_eq!(bat.inversions,1);
 }
}
fn main(){}
