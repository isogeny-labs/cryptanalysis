'use strict';
// Independent centralizer/norm method rather than Python's 4-entry matrix census.
const n=4,p=101,t=-7,t2=-11;
const m=(x,k=n)=>((x%k)+k)%k;
const F=[[0,m(-p)],[1,m(t)]];
const apply=(U,v)=>[m(U[0][0]*v[0]+U[0][1]*v[1]),m(U[1][0]*v[0]+U[1][1]*v[1])];
const wedge=(v,w)=>m(v[0]*w[1]-v[1]*w[0]);
const vectors=Array.from({length:16},(_,i)=>[i%4,Math.floor(i/4)]);
function check(v,s){if(!v)throw Error(s);}
let anti=[],ordinary=[];
for(let a=0;a<4;a++)for(let b=0;b<4;b++){
  const U=[[a,m(-p*b)],[b,m(a+t*b)]];
  const det=m(a*a+t*a*b+p*b*b);
  if(det%2===0)continue;
  (det===3?anti:ordinary).push([a,b]);
  for(const v of vectors){
    const x=apply(F,apply(U,v)),y=apply(U,apply(F,v));
    check(x[0]===y[0]&&x[1]===y[1],"F commutation");
    for(const w of vectors)
      check(wedge(apply(U,v),apply(U,w))===m(det*wedge(v,w)),"Weil form scaling");
  }
}
check(anti.length===6&&ordinary.length===6,"centralizer norm census");
const sign=new Set(anti.map(([a,b])=>[a+','+b,m(-a)+','+m(-b)].sort()[0]));
check(sign.size===3,"sign quotient");
check(m(t,4)===m(t2,4)&&m(t,8)!==m(t2,8),"trace discrimination");
check(m(t,4)!==m(t2+1,4),"trace mutant");
console.log("CT43 JS independent PASS [pcc:unverified]");
console.log("centralizer units 12; determinant 1: 6, determinant 3: 6");
console.log("F-stable Weil-anti candidates 6, sign-pairs 3; modulo8 trace mismatch");
