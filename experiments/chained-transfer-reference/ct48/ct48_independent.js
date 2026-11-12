'use strict';
// CT48 independently written finite-local-ring diagonalization [pcc:unverified].
const requireTrue = (c,m) => {if (!c) throw Error(m)};
const mod = (a,m) => ((a%m)+m)%m;
const valuation = x => {requireTrue(x!==0n,'v2 zero');let v=0;while ((x&1n)===0n){x>>=1n;v++;}return v};
const times = (A,B,m) => [
  mod(A[0]*B[0]+A[1]*B[2],m),mod(A[0]*B[1]+A[1]*B[3],m),
  mod(A[2]*B[0]+A[3]*B[2],m),mod(A[2]*B[1]+A[3]*B[3],m)
];
function frobenius(t,k,m){
  let a=[0n,mod(-101n,m),1n,mod(BigInt(t),m)],o=[1n,0n,0n,1n];
  let n=BigInt(k);
  while(n>0n){if(n&1n)o=times(o,a,m);a=times(a,a,m);n>>=1n;}
  return o;
}
function linearMap(k,m,t1=-11){
  const A=frobenius(-7,k,m), B=frobenius(t1,k,m);
  const L=Array.from({length:4},()=>Array(4).fill(0n));
  for(let j=0;j<4;j++){
    const X=[0n,0n,0n,0n];X[j]=1n;
    const BX=times(B,X,m),XA=times(X,A,m);
    for(let i=0;i<4;i++)L[i][j]=mod(BX[i]-XA[i],m);
  }
  return L;
}
function oddInverse(a,m){
  requireTrue((a&1n)===1n,'odd unit required');
  let inv=1n;
  for(let h=1; (1n<<BigInt(h))<m; h*=2) inv=mod(inv*(2n-a*inv),m);
  inv=mod(inv*(2n-a*inv),m);
  requireTrue(mod(inv*a,m)===1n,'inverse error');
  return inv;
}
function localDiagonal(k, trace=-11){
  const r=valuation(BigInt(k)),cap=4*r+18,m=1n<<BigInt(cap);
  const L=linearMap(k,m,trace),vals=[];
  for(let j=0;j<4;j++){
    let u=-1,v=-1,small=cap;
    for(let a=j;a<4;a++)for(let b=j;b<4;b++){
      if(L[a][b]!==0n && valuation(L[a][b])<small){small=valuation(L[a][b]);u=a;v=b;}
    }
    requireTrue(u>=0,'valuation precision too low');
    [L[j],L[u]]=[L[u],L[j]];
    for(let i=0;i<4;i++)[L[i][j],L[i][v]]=[L[i][v],L[i][j]];
    const pow=1n<<BigInt(small);
    const inv=oddInverse(L[j][j]/pow,m);
    for(let b=0;b<4;b++)L[j][b]=mod(L[j][b]*inv,m);
    requireTrue(L[j][j]===pow,'pivot normalization');
    for(let a=j+1;a<4;a++){
      requireTrue(L[a][j]%pow===0n,'nondivisible below pivot');
      const coeff=L[a][j]/pow;
      for(let b=0;b<4;b++)L[a][b]=mod(L[a][b]-coeff*L[j][b],m);
    }
    for(let b=j+1;b<4;b++){
      requireTrue(L[j][b]%pow===0n,'nondivisible right of pivot');
      const coeff=L[j][b]/pow;
      for(let a=0;a<4;a++)L[a][b]=mod(L[a][b]-coeff*L[a][j],m);
    }
    vals.push(small);
  }
  return vals;
}
function want(k){const r=valuation(BigInt(k));return k%3?[0,0,r+2,r+2]:[r+2,r+2,r+3,r+3]}
const cases=new Set();for(let k=1;k<=96;k++)cases.add(k);
for(let r=0;r<=16;r++){cases.add(2**r);cases.add(3*2**r);if(r<10){cases.add(5*2**r);cases.add(15*2**r)}}
const keys=[...cases].sort((a,b)=>a-b);
for(const k of keys){
  const got=localDiagonal(k),exp=want(k);
  requireTrue(JSON.stringify(got)===JSON.stringify(exp),'k='+k+' '+got+' != '+exp);
}
requireTrue(JSON.stringify(localDiagonal(1,-15))!==JSON.stringify(want(1)),'trace mutant accepted');
const count=(k,s)=>2**want(k).reduce((a,v)=>a+Math.min(s,v),0);
requireTrue(count(1,8)===16 && count(3,8)===1024,'count sanity');
console.log('CT48 PASS [pcc:unverified]');
console.log('smith_cases='+keys.length+'; independent_2adic_pivot_reductions='+(4*keys.length)+'; trace_mutant_rejected=1');
console.log('k=1: smith_2=[0,0,2,2], hom(E[256],F[256])=16');
console.log('k=3: smith_2=[2,2,3,3], hom(E[256],F[256])=1024');
