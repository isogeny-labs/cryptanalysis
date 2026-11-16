#!/usr/bin/env node
// CT166 independently implemented CM obstruction audit. Source-only, [pcc:unverified].
// Unlike the Python checker, squarefree reduction uses square-divisor stripping.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const P=223, Q=P**3, N=11086844;
const expectedBlob="9a8fb44420385a67eda841e68c4c70c13aedcdb8";
function must(condition, message) { if (!condition) throw new Error(message); }
function isPrime(n) {
  if (!Number.isSafeInteger(n) || n<2) return false;
  for (let d=2; d*d<=n; d++) if(n%d===0) return false;
  return true;
}
function squarefree(n) {
  must(Number.isSafeInteger(n)&&n!==0,"squarefree integer");
  const sign=n<0?-1:1; let v=Math.abs(n);
  for(let d=2; d*d<=v;d++) {
    while(v%(d*d)===0) v/=(d*d);
  }
  return sign*v;
}
function factor(n) {
  must(Number.isSafeInteger(n)&&n>0,"factor integer");
  let v=n, out=[];
  for(let d=2;d*d<=v;d++) {
    if(v%d!==0) continue;
    let e=0; while(v%d===0){v/=d;e++;}
    must(isPrime(d),"factor not prime");
    out.push([d,e]);
  }
  if(v>1){must(isPrime(v),"last factor not prime");out.push([v,1]);}
  return out;
}
function canonical(o) {
  if(Array.isArray(o)) return "["+o.map(canonical).join(",")+"]";
  if(o!==null && typeof o==="object")
    return "{"+Object.keys(o).sort().map(k=>JSON.stringify(k)+":"+canonical(o[k])).join(",")+"}";
  return JSON.stringify(o);
}
function readCensus(folder) {
  const b=fs.readFileSync(path.join(folder,"CT160_FULL_CENSUS.json"));
  const header=Buffer.from("blob "+b.length+"\0");
  const sha=crypto.createHash("sha1").update(header).update(b).digest("hex");
  must(sha===expectedBlob,"changed CT160 source Git blob");
  const obj=JSON.parse(b.toString("utf8"));
  return obj;
}
function check(data){
  must(data && data.schema==="ct160-fixed-nu12-whole-field-census/v1","schema");
  must(Number.isInteger(data.field_cardinality)&&data.field_cardinality===Q,"field");
  must(data.accepted===true && data.mutant===false && data.mutation_rejected===false, "nominal flags");
  must(data.square_roster_cardinality===(Q+1)/2,"square roster");
  for(const name of ["actual_fixed_nu12_source","actual_fixed_nu12_target"]){
    const m=data[name]; must(m && typeof m==="object","missing model");
    for(const key of ["zeros","nonzero_squares","nonsquares","order"])
      must(Number.isSafeInteger(m[key]),"noninteger model field");
    must(m.zeros + m.nonzero_squares + m.nonsquares===Q,"field population");
    must(2*m.nonzero_squares+m.zeros+1===m.order && m.order===N,"point count");
  }
  const T=Q+1-N, D=T*T-4*Q;
  must(T===2724&&T%P!==0&&D===-36938092,"trace/discriminant");
  const targetFactors=factor(-D/4);
  must(canonical(targetFactors)===canonical([[23,1],[311,1],[1291,1]]),"squarefree target primes");
  const cm=squarefree(D);
  must(cm===-9234523,"target CM field");
  const H=Math.floor(Math.sqrt(4*P));
  const traces=Array.from({length:2*H+1},(_,i)=>i-H);
  must(traces.length===59,"Hasse roster");
  const ordinary=traces.filter(t=>t%P!==0);
  must(ordinary.length===58,"ordinary roster");
  let maxRadicand=0;
  for(const t of ordinary){
    const sourceDelta=t*t-4*P;
    const sourceRadicand=squarefree(sourceDelta);
    maxRadicand=Math.max(maxRadicand,Math.abs(sourceRadicand));
    must(Math.abs(sourceRadicand)<Math.abs(cm),"unexpected CM collision");
  }
  must(maxRadicand===883,"source maximum");
  const t=4, baseChangeT3=t*t*t-3*P*t;
  must(baseChangeT3===-2612 && squarefree(baseChangeT3**2-4*Q)===-219 &&
    squarefree(t*t-4*P)===-219, "positive base-change collision");
  return {
    schema:"ct166-geometric-cm-obstruction/v1",
    source_base_field:P,
    source_extension_field:Q,
    actual_endpoint_order:N,
    actual_endpoint_trace:T,
    actual_endpoint_discriminant:D,
    target_cm_squarefree_radicand:cm,
    target_cm_factorization:targetFactors,
    hasse_traces_checked:traces.length,
    ordinary_source_traces_checked:ordinary.length,
    supersingular_source_traces:[0],
    maximum_ordinary_source_cm_radicand_abs:maxRadicand,
    positive_base_change_trace:baseChangeT3,
    positive_base_change_cm_radicand:-219,
    geometric_algebraic_hom_possible:false,
    scope:"elliptic source over F223 to actual fixed-nu12 elliptic endpoints or their Weil-restriction F223-isogeny class, after any finite scalar extension",
    standing:"[pcc:unverified]; source-only integer/CM proof, no independent native ECDLP timing"
  };
}
function negativeTests(data){
  const controls=[
    ["source_order", x=>x.actual_fixed_nu12_source.order=N+1],
    ["target_zeros", x=>x.actual_fixed_nu12_target.zeros=4],
    ["boolean_order", x=>x.actual_fixed_nu12_source.order=true],
    ["wrong_field", x=>x.field_cardinality=Q+1],
    ["missing_model", x=>delete x.actual_fixed_nu12_target],
  ], rejected=[];
  for(const [name,change] of controls) {
    const x=structuredClone(data); change(x);
    try {check(x);} catch(e) {rejected.push(name);continue;}
    throw new Error("falsely accepted: "+name);
  }
  // The source Git-blob check, rather than JS's permissive JSON parser,
  // rejects duplicate keys/NaN/float if an attacker changes the fixture.
  // Make these parser-boundary cases explicit, not a false strict-parser claim.
  for(const [name,raw] of [
    ["duplicate_keys",'{"x":1,"x":2}'],
    ["nan",'{"x":NaN}'],
    ["infinite",'{"x":Infinity}'],
    ["float",'{"x":1.0}']
  ]){
    const blob=Buffer.from(raw);
    const sha=crypto.createHash("sha1").update(Buffer.from("blob "+blob.length+"\0")).update(blob).digest("hex");
    must(sha!==expectedBlob,"forged raw input SHA");
    rejected.push(name);
  }
  return rejected;
}
const folder=process.argv[2]||path.dirname(new URL(import.meta.url).pathname);
const data=readCensus(folder);
const result=check(data);
if(process.argv.includes("--self-test")) result.negative_controls_rejected=negativeTests(data);
process.stdout.write(canonical(result)+"\n");
