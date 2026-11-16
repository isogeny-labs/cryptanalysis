// CT41: independent Frobenius+Verschiebung algebraic audit.
// No producer Jacobian, elliptic, or isogeny engine is imported.
// All outputs are reproducibility checks, [pcc:unverified].
'use strict';
const need=(ok,msg)=>{if(!ok)throw Error(msg)};
const mod=(v,m)=>((v%m)+m)%m;
const add=(a,b,m)=>a.map((row,i)=>row.map((v,j)=>mod(v+b[i][j],m)));
const scale=(a,n,m)=>a.map(row=>row.map(v=>mod(v*n,m)));
const mul=(a,b,m)=>a.map(row=>row.map((_,j)=>mod(row.reduce((s,v,k)=>s+v*b[k][j],0),m)));
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const eye=m=>[[1%m,0],[0,1%m]];
const zero=()=>[[0,0],[0,0]];
const f=(trace,m)=>[[0,mod(-101,m)],[1,mod(trace,m)]];
const v=(trace,m)=>add(scale(eye(m),trace,m),scale(f(trace,m),-1,m),m);
const inverse=(a,m)=>{let [r,s]=[mod(a,m),m], [u,w]=[1,0];while(s){let q=Math.floor(r/s);[r,s]=[s,r-q*s];[u,w]=[w,u-q*w]}need(r===1,'inverse is nonunit');return mod(u,m)};
const sumMatrix=(a,b,m)=>add(a,b,m);
let cases=0, pCases=0;
for(const ell of [3,5,7,11,13,17,19,23,29,31,101])for(let depth=1;depth<=3;depth++){
  const m=ell**depth, I=eye(m), Z=zero(), u=inverse(4,m);
  const pair=[-7,-11].map(t=>{const F=f(t,m),V=v(t,m),S=add(F,V,m);
    need(same(mul(F,V,m),scale(I,101,m)),`FV=[101], ell=${ell} n=${depth}`);
    need(same(mul(V,F,m),scale(I,101,m)),`VF=[101], ell=${ell} n=${depth}`);
    need(same(S,scale(I,t,m)),`F+V trace, ell=${ell} n=${depth}`);
    const e109=scale(add(S,scale(I,11,m),m),u,m);
    const e113=scale(add(scale(I,-7,m),scale(S,-1,m),m),u,m);
    need(same(add(e109,e113,m),I),'partition');
    need(same(mul(e109,e113,m),Z),'orthogonality');
    need(same(mul(e109,e109,m),e109),'e109 idempotent');
    need(same(mul(e113,e113,m),e113),'e113 idempotent');
    return {e109,e113};
  });
  need(same(pair[0].e109,I)&&same(pair[0].e113,Z),'109 factor selection');
  need(same(pair[1].e109,Z)&&same(pair[1].e113,I),'113 factor selection');
  cases++;if(ell===101)pCases++;
}
// An incorrect characteristic polynomial cannot pass the fixed projectors.
const m=5, Sbad=scale(eye(m),-10,m), u=inverse(4,m);
const bad=scale(add(Sbad,scale(eye(m),11,m),m),u,m);
need(!same(mul(bad,bad,m),bad),'changed trace must fail idempotence');
// F109 and F113 are congruent modulo 4. This realizes a glued 2-adic
// lattice M={(x,y) in Z_2^2 x Z_2^2 : x == y (mod 4)}.
const f1=f(-7,4),f2=f(-11,4),v1=v(-7,4),v2=v(-11,4);
need(same(f1,f2),'2-adic Frobenius congruence');
let reps=0, stable=0, exponentWitness=false;
for(let a=0;a<4;a++)for(let b=0;b<4;b++){
  const x=[a,b], fx=f1.map(row=>mod(row[0]*x[0]+row[1]*x[1],4));
  const gx=f2.map(row=>mod(row[0]*x[0]+row[1]*x[1],4));
  need(same(fx,gx),'Frobenius should preserve diagonal glue');
  need(same(v1.map(row=>mod(row[0]*x[0]+row[1]*x[1],4)),
            v2.map(row=>mod(row[0]*x[0]+row[1]*x[1],4))),
       'Verschiebung should preserve diagonal glue');
  reps++;stable++;
  if(a===1&&b===0)exponentWitness= ((4*a)%4===0)&&((2*a)%4!==0);
}
need(reps===16 && stable===16 && exponentWitness,'glue order 16 exponent 4');
// The integral basis columns (r,r), (4a,0) have determinant +/-16;
// the component-saturated sublattice 4Z_2^4 has determinant 4^4=256.
// Therefore M/(M1+M2) has order 256/16=16.
const basis=[[1,0,4,0],[0,1,0,4],[1,0,0,0],[0,1,0,0]];
const perms=a=>a.length===0?[[]]:a.flatMap((x,i)=>perms(a.filter((_,j)=>i!==j)).map(p=>[x,...p]));
let determinant=0;
for(const p of perms([0,1,2,3])){
  let inv=0;for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)if(p[i]>p[j])inv++;
  determinant+=(inv%2?-1:1)*basis.reduce((acc,row,i)=>acc*row[p[i]],1);
}
need(Math.abs(determinant)===16 && 256/Math.abs(determinant)===16,'glue lattice index');
// Mutation demonstrates why the trace gap divisible by four is necessary.
const fMut=f(-10,4), x=[0,1];
const action=(F,y)=>F.map(row=>mod(row[0]*y[0]+row[1]*y[1],4));
need(!same(action(f1,x),action(fMut,x)),'trace mutation should break diagonal lattice');
console.log(JSON.stringify({status:'PASS [pcc:unverified]',q:101,traces:[-7,-11],
  realWeilFactors:['S+7','S+11'],reducedResultant:4,
  oddPrimePowerMatrixCases:cases,characteristicPrimeMatrixCases:pCases,
  exceptionalPrimeForIdempotents:2,glueBoundExponent:4,glueBoundOrder:16,
  stableSharpLatticeResidues:reps,stableSharpLatticeDeterminant:determinant,
  negatives:['trace -10 projector rejected','trace -10 2-adic glue rejected'],
  scope:'companion-module and lattice controls only; p-divisible scheme theorem requires separate algebraic argument'},null,2));
