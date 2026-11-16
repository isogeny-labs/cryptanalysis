#!/usr/bin/env node
'use strict';
// CT164. Independent mod-4 finite-coset enumeration; no lattice-basis dependency.
const fs=require('fs'), path=require('path');
const K=[['factorwise',[1,4,16]],['factorwise',[2,8,32]],['factorwise',[3,12,48]],['mixed',[5,17,42]],['mixed',[5,17,43]],['mixed',[10,21,34]],['mixed',[10,23,34]],['mixed',[15,21,38]],['mixed',[15,22,37]]];
const MS=[[[0,1],[1,1]],[[1,1],[1,0]]];
const ensure=(cond,msg)=>{if(!cond)throw Error(msg)};
const pair=(a,b)=>{let x=0;for(let i=0;i<3;i++)x^=(((a>>(2*i))&1)&((b>>(2*i+1))&1))^(((a>>(2*i+1))&1)&((b>>(2*i))&1));return x};
const frob2=v=>((v<<2)&63)|(v>>>4);
const validM=m=>(m[0][0]+m[1][1])%2===1&&((m[0][0]*m[1][1]-m[0][1]*m[1][0])&1)===1;
const bits=v=>Array.from({length:6},(_,i)=>(v>>i)&1);
const enc=v=>v.reduce((sum,x,i)=>sum+(x<<(2*i)),0);
const add=(a,b)=>a.map((x,i)=>(x+b[i])&3);
const mul2=x=>bits(x).map(y=>2*y);
const hspan=gens=>{
 let s=new Set([0]);for(const g of gens)for(const h of [...s])s.add(g^h);
 return [...s].sort((a,b)=>a-b);
};
const frob=(v,m)=>{
 let t=[];for(let i=0;i<2;i++)t.push((v[4+i]+2*m[i][0]*v[4]+2*m[i][1]*v[5])&3);
 return [...t,...v.slice(0,4)];
};
const can=(x,h)=>Math.min(...h.map(v=>enc(add(x,mul2(v)))));
function solve(){
 const data=JSON.parse(fs.readFileSync(path.join(__dirname,'CT163_RESULT.json'),'utf8'));
 ensure(data.schema==='ct163-galois-stable-lagrangian/v1'&&data.frobenius_stable_lagrangians===9,'CT163 schema');
 ensure(data.assumption.group_order===11086844&&data.assumption.nu12_full_two_torsion_size===4,'source order/2-torsion');
 ensure(JSON.stringify(data.kernels.map(r=>[r.kind,r.basis]))===JSON.stringify(K),'CT163 input kernel mismatch');
 const records=[];
 for(const [kind,basis] of K){
  const h=hspan(basis);
  ensure(h.length===8,'rank3');
  ensure(h.every(a=>h.every(b=>pair(a,b)===0)),'non-isotropic kernel');
  ensure(h.every(v=>h.includes(frob2(v))),'non-stable kernel');
  const sizes=[];
  for(const m of MS){ensure(validM(m),'bad mod-4 Frobenius lift');
    const s=new Map();
    for(const hval of h)for(let u=0;u<64;u++){
      const z=add(bits(hval),mul2(u));
      const key=can(z,h);
      if(!s.has(key))s.set(key,z);
    }
    if(s.size!==64)throw Error('quotient must have 64 classes');
    let fixed=0;
    for(const [key,z] of s){
      const transformed=can(frob(z,m),h);
      if(!s.has(transformed))throw Error('nonstable quotient');
      if(key===transformed)fixed++;
    }
    if(fixed!==2)throw Error('unexpected rational 2 torsion for '+basis+' ='+fixed);
    sizes.push(fixed);
  }
  records.push({basis,kind,rational_2_torsion_size_by_m:sizes,cyclic_2_sylow:true});
 }
 return {schema:'ct164-even-degree-quotient-two-torsion/v1',field:223,extension_degree:3,full_curve_order:11086844,cubic_trace:2724,m_lifts:MS,kernels:records,rational_2_torsion_size:2,hyperelliptic_genus3_necessary_orbits:[[1,1,6],[2,3,3]],standing:'[pcc:unverified]; mod-4 Tate module screen only'};
}
const o=solve();
if(process.argv.includes('--self-test')){
 const reject=fn=>{try{fn();return false}catch(e){return true}};
 const controls=[
   ()=>ensure(hspan([1,4]).length===8,'rank mutation'),
   ()=>ensure(hspan([1,2,4]).every(a=>hspan([1,2,4]).every(b=>pair(a,b)===0)),'nonisotropic'),
   ()=>ensure(hspan([1,4,32]).every(v=>hspan([1,4,32]).includes(frob2(v))),'nonstable'),
   ()=>ensure(validM([[0,0],[0,0]]),'invalid lift'),
   ()=>ensure((11086844+4)%8===4,'wrong two Sylow')
 ];
 ensure(controls.every(reject),'mutant accepted');o.negative_controls_rejected=controls.length;
}
const sorted=x=>Array.isArray(x)?x.map(sorted):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,sorted(x[k])])):x;
process.stdout.write(JSON.stringify(sorted(o))+'\n');
