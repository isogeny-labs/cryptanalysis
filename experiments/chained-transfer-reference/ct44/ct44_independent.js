'use strict';
// CT44 independent algebra in R=Z/4[F]/(F^2-F+1), not Python matrices.
const n = x => (x % 4 + 4) % 4;
const mul = ([a,b],[c,d]) => [n(a*c-b*d), n(a*d+b*c+b*d)];
const norm = ([a,b]) => n(a*a+a*b+b*b);
const adj = ([a,b]) => [n(a+b),n(-b)];
const inv = x => {
  const d=norm(x);
  if (d!==1 && d!==3) throw Error('nonunit');
  return adj(x).map(v=>n(d*v));
};
const eq = (a,b) => a[0]===b[0]&&a[1]===b[1];
const units = [], degree7=[], degree49=[];
for(let a=0;a<4;a++) for(let b=0;b<4;b++) {
 const x=[a,b], d=norm(x);
 if (d%2) units.push(x);
 if(d===3) degree7.push(x);
 if(d===1) degree49.push(x);
}
if(units.length!==12||degree7.length!==6||degree49.length!==6) throw Error('census');
const one=[1,0];
let duals=0;
for(const a of degree7){
 if(!degree7.some(x=>eq(x,adj(a)))) throw Error('adj degree');
 if(!eq(mul(a,adj(a)),[3,0])) throw Error('degree7 dual');
 duals++;
}
let transports=0, bad=0, towers=0;
const set = arr=>new Set(arr.map(x=>x.join(',')));
const s7=set(degree7), s49=set(degree49);
for (const a of degree7) for(const b of degree7) for(const u of degree7){
 const v=mul(mul(b,u),inv(a));
 if(!s7.has(v.join(','))) throw Error('one hop anti graph');
 transports++;
}
for (const a of degree7) for(const b of degree49) for(const u of degree7){
 const v=mul(mul(b,u),inv(a));
 if(!s49.has(v.join(','))) throw Error('wrong degree not detected');
 // Mod 2 cannot distinguish det=1 from det=3 (both reduce to 1).
 if(norm(v)%2!==1) throw Error('mod 2 negative control');
 bad++;
}
for(const a of degree7) for(const b of degree7)
 for(const c of degree7) for(const d of degree7)
 for(const u of degree7){
  const ac=mul(b,a), bd=mul(d,c), first=mul(mul(c,u),inv(a));
  const via=mul(mul(d,first),inv(b));
  const direct=mul(mul(bd,u),inv(ac));
  if(!eq(via,direct)||norm(ac)!==1||norm(bd)!==1||norm(via)!==3)
   throw Error('two-hop covariance');
  if(!eq(mul(ac,adj(ac)),one))throw Error('degree49 adjugate');
  towers++;
 }
if(duals!==6||transports!==216||bad!==216||towers!==7776)throw Error('totals');
console.log('PASS CT44 [pcc:unverified]: 6 degree-7 norm-3 units; 6 degree-49 norm-1 units; 6 adjugate duals');
console.log('PASS CT44: 216 ring-theoretic one-hop transports, 7776 two-hop transports; 216 wrong-degree controls');
console.log('BOUNDARY: independent commutative ring verifier; no actual native elliptic map identified');
