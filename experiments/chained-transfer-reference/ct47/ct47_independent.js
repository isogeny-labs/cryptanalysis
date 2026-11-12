#!/usr/bin/env node
'use strict';
// Independently constructed modular matrix audit of CT47 [pcc:unverified].
function requireTrue(ok,msg){if(!ok)throw Error(msg)}
const p=101;
const prod=(a,b,m)=>[
 (a[0]*b[0]+a[1]*b[2])%m,(a[0]*b[1]+a[1]*b[3])%m,
 (a[2]*b[0]+a[3]*b[2])%m,(a[2]*b[1]+a[3]*b[3])%m];
const eye=[1,0,0,1];
function power(a,n,m){let b=eye;while(n>0){if(n%2)b=prod(b,a,m);a=prod(a,a,m);n=Math.floor(n/2)}return b}
const frob=(t,m)=>[0,(m-p%m)%m,1,((t%m)+m)%m];
const determinant=(a,m)=>((a[0]*a[3]-a[1]*a[2])%m+m)%m;
const equal=(a,b)=>a.every((v,i)=>v===b[i]);
const swap=[0,1,1,0];
function validate(k,s){
 const m=2**s,E=power(frob(-7,m),k,m),F=power(frob(-11,m),k,m);
 const r=Math.log2(k&-k)|0;
 const depth=r+(k%3===0?3:2);
 if(s<=depth){
  if(k%3===0){
   requireTrue(equal(prod(swap,E,m),prod(F,swap,m)),`swap fail ${k}, ${s}`);
  } else {
   const inv=(x)=>{for(let y=1;y<m;y+=2)if(x*y%m===1)return y;throw Error('inverse')};
   const x=E[2],y=F[2];requireTrue(x%2===1 && y%2===1,'noncyclic Frobenius');
   const B=[1,((F[0]-E[0])*inv(x)%m+m)%m,0,y*inv(x)%m];
   requireTrue(equal(prod(B,E,m),prod(F,B,m)),`basis fail ${k}, ${s}`);
   const invdet=inv(determinant(B,m)),target=(m-invdet)%m;
   let b=0;
   for(let h=1;h<s;h++){
     let mod=2**(h+1);
     if((1-7*b+101*b*b-target)%mod!==0)b+=2**h;
     requireTrue(((1-7*b+101*b*b-target)%mod+mod)%mod===0,'norm lift');
   }
   const C=frob(-7,m),Z=[1,(b*C[1])%m,b%m,((1+b*C[3])%m+m)%m];
   const V=prod(B,Z,m);
   requireTrue(determinant(V,m)===m-1,'Weil determinant');
   requireTrue(equal(prod(V,E,m),prod(F,V,m)),'anti-isometry failed');
  }
 }
 return depth;
}
function normalized(t,k,r,scalar){
 const m=2**(r+4),d=2**(r+2),A=power(frob(t,m),k,m),N=[];
 for(let i=0;i<4;i++){
  const diff=((A[i]-(i===0||i===3?scalar:0))%m+m)%m;
  requireTrue(diff%d===0,'normalization invalid');
  N.push(Math.floor(diff/d)%4);
 }
 return determinant(N,4);
}
for(let r=0;r<=9;r++){
 const k=3*2**r;
 requireTrue(validate(k,r+3)===r+3,'depth');
 const a=normalized(-7,k,r,r===0?3:1),b=normalized(-11,k,r,r===0?3:1);
 requireTrue(a===(r===0?1:3) && b===(r===0?3:1),`det invariant ${k} ${a} ${b}`);
}
for(let r=0;r<=10;r++){
 const k=2**r;
 requireTrue(validate(k,r+2)===r+2,'cyclic case');
}
for(let k=1;k<=31;k++){
 for(let s=1;s<=Math.min(7,Math.floor(Math.log2(k&-k))+(k%3===0?3:2));s++)
   validate(k,s);
}
requireTrue(validate(2,3)===3 && validate(3,3)===3 && validate(4,4)===4,'k-specific depths');
requireTrue(normalized(-7,3,0,3)!==normalized(-11,3,0,3),'trace-only false positive');
console.log('CT47 JS PASS [pcc:unverified]');
console.log('all k=1..31 positive depths, r<=10 power-two witnesses, r<=9 3-power witnesses/obstructions');
