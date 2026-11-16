#!/usr/bin/env node
// Independent RREF (not triple-span) enumeration of the fixed level-2 module.
const ensure=(ok,msg)=>{if(!ok)throw new Error(msg)};
const span=rows=>{
  let s=new Set([0]);
  for(const row of rows){const old=[...s];for(const x of old)s.add(x^row)}
  return [...s].sort((a,b)=>a-b)
};
const symp=(a,b)=>{
  let t=0;for(let i=0;i<3;i++){
    t^=(((a>>(2*i))&1)&((b>>(2*i+1))&1));
    t^=(((a>>(2*i+1))&1)&((b>>(2*i))&1))
  }return t
};
const frob=x=>((x<<2)&63)|(x>>>4);
const key=s=>[...s].sort((a,b)=>a-b).join(",");
const iso=(s,form=symp)=>s.every(a=>s.every(b=>form(a,b)===0));
const stable=(s,act=frob)=>key(s.map(act))===key(s);
function choose(n,k,start=0){
  if(k===0)return [[]];
  let out=[];
  for(let i=start;i<=n-k;i++)
    for(const tail of choose(n,k-1,i+1))out.push([i,...tail]);
  return out
}
function rrefSubspaces(){
  const result=new Map();
  for(const ps of choose(6,3)){
    const choices=ps.map(p=>{
      const free=Array.from({length:5-p},(_,i)=>p+i+1).filter(j=>!ps.includes(j));
      return Array.from({length:1<<free.length},(_,m)=>
        free.reduce((v,j,i)=>v|(((m>>i)&1)<<j),1<<p))
    });
    for(const x of choices[0])for(const y of choices[1])for(const z of choices[2]){
      const s=span([x,y,z]);
      ensure(s.length===8,"bad RREF rank");
      result.set(key(s),s)
    }
  }
  ensure(result.size===1395,"Gaussian binomial count");
  return [...result.values()]
}
const basis=s=>{
  let b=[],t=new Set([0]);
  for(const v of s)if(!t.has(v)){
    b.push(v);for(const x of [...t])t.add(x^v)
  }return b
};
const local=s=>[0,1,2].map(i=>s.filter(v=>(v&(~(3<<(2*i))&63))===0).length);
const cmp=(a,b)=>{
  for(let i=0;i<8;i++)if(a[i]!==b[i])return a[i]-b[i];
  return 0
};
function solve(){
  const all=rrefSubspaces(), lags=all.filter(iso);
  ensure(lags.length===135,"Lagrangian count");
  const selected=lags.filter(s=>stable(s)).sort(cmp);
  ensure(selected.length===9,"Galois-stable count");
  const kernels=selected.map(s=>{
    const ls=local(s);
    ensure(ls.every(x=>x===1||x===2),"factor support");
    const kind=ls.every(x=>x===2)?"factorwise":"mixed";
    return {span:s,basis:basis(s),kind,local_sizes:ls,
            frobenius_fixed:s.filter(x=>frob(x)===x).length}
  });
  ensure(kernels.filter(x=>x.kind==="mixed").length===6,"mixed count");
  ensure(kernels.filter(x=>x.kind==="factorwise").length===3,"factorwise count");
  ensure(kernels.every(x=>x.frobenius_fixed===2),"fixed group size");
  return {schema:"ct163-galois-stable-lagrangian/v1",
          assumption:{p:223,extension_degree:3,nu12_full_two_torsion_size:4,
                      weierstrass_roots:3,group_order:11086844},
          all_three_subspaces:1395,lagrangian_subspaces:135,
          frobenius_stable_lagrangians:9,factorwise:3,mixed:6,kernels,
          status:"[pcc:unverified]; finite 2-torsion kernels only, no Jacobian or DLP speedup"}
}
function selfTest(o){
  ensure(!iso(span([1,2,4])),"accepted nonisotropic");
  ensure(span([1,4]).length!==8,"accepted wrong dimension");
  ensure(!stable(span([1,4,32])),"accepted nonstable");
  const all=rrefSubspaces();
  ensure(all.filter(s=>iso(s,()=>0)).length!==135,"accepted wrong pairing");
  ensure(all.filter(iso).filter(s=>stable(s,x=>x)).length!==9,"accepted wrong action");
  ensure({...o.assumption,nu12_full_two_torsion_size:2}.nu12_full_two_torsion_size!==4,
         "accepted false full two torsion");
  return 6
}
const sorted=v=>Array.isArray(v)?v.map(sorted):v&&typeof v==="object"?
  Object.fromEntries(Object.keys(v).sort().map(k=>[k,sorted(v[k])])):v;
const o=solve();
if(process.argv.includes("--self-test"))o.negative_controls_rejected=selfTest(o);
process.stdout.write(JSON.stringify(sorted(o))+"\n");
