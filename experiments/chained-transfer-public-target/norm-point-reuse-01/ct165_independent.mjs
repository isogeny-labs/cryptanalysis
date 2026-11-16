// CT165 independently structured prime-field ECDLP subgroup obstruction.
// Does not call the Python implementation. Run with 'node ct165_independent.mjs DIR'.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const folder=process.argv[2]||'.';
const specs={
 census:['CT160_FULL_CENSUS.json','9a8fb44420385a67eda841e68c4c70c13aedcdb8'],
 audit:['CT160_GENERATOR_AUDIT.json','84086b49178ca298779c771eff1aaeacb3728beb'],
 kernels:['CT163_RESULT.json','1b93b009b1380a6ccbc677ae0d3e6fb7a4decfa9'],
 quotients:['CT164_RESULT.json','e9f7fafedb7b83c21566edfefa6bfcdaf234e6ba'],
};
function must(b,msg){if(!b)throw new Error(msg)}
function blobHash(buf){return crypto.createHash('sha1').update('blob '+buf.length+'\0').update(buf).digest('hex')}
const A={};
for(const [key,[file,expected]] of Object.entries(specs)){
 const content=fs.readFileSync(path.join(folder,file));
 must(blobHash(content)===expected,'changed Git blob '+file);
 A[key]=JSON.parse(content.toString('utf8'));
}
function divisors(n){const result=[];for(let x=2; x*x<=n; x++){while(n%x===0){result.push(x);n/=x}}if(n>1)result.push(n);return result}
function gcdEuclid(a,b){while(b){[a,b]=[b,a%b]}return a}
function verify(A){
 const p=223, cube=p*p*p, n=11086844,r=2771711;
 must(A.census.schema==='ct160-fixed-nu12-whole-field-census/v1'&&A.census.field_cardinality===cube,'source field');
 for(const tag of ['actual_fixed_nu12_source','actual_fixed_nu12_target']){
   const v=A.census[tag];must(v&&Object.values(v).every(Number.isSafeInteger),'counts type');
   must(v.order===n&&v.zeros+v.nonzero_squares+v.nonsquares===cube,'counts population');
   must(2*v.nonzero_squares+v.zeros+1===n,'sum of y solutions');
 }
 must(A.audit.field_size===cube&&A.audit.cubic_trace===cube+1-n,'source trace');
 must(A.audit.model_generators.length===2&&new Set(A.audit.model_generators.map(v=>v.model)).size===2,'generators');
 for(const v of A.audit.model_generators){must(v.generator_prime_order===r&&v.group_order===n&&v.on_curve===true,'generator order')}
 const pf=divisors(r);must(pf.length===1&&pf[0]===r&&n===4*r,'prime factor');
 must(A.kernels.assumption.p===p&&A.kernels.assumption.extension_degree===3&&A.kernels.assumption.group_order===n,'kernel source');
 must(A.kernels.frobenius_stable_lagrangians===9&&A.kernels.factorwise===3&&A.kernels.mixed===6,'kernel counts');
 must(A.quotients.schema==='ct164-even-degree-quotient-two-torsion/v1'&&A.quotients.field===p&&A.quotients.extension_degree===3&&A.quotients.full_curve_order===n&&A.quotients.rational_2_torsion_size===2,'quotients');
 const x=A.kernels.kernels,y=A.quotients.kernels;
 must(x.length===9&&y.length===9,'kernel population');
 must(new Set(x.map(k=>k.basis.join(','))).size===9,'duplicate kernel');
 for(let i=0;i<9;i++){must(x[i].basis.join()===y[i].basis.join()&&x[i].kind===y[i].kind,'kernel match');must(y[i].rational_2_torsion_size_by_m.join() === '2,2','quotient 2 torsion')}
 // Independent integer sqrt by monotone search; cannot rely on Python isqrt.
 let delta=0;while((delta+1)*(delta+1)<=4*p)delta++;
 const low=p+1-delta, high=p+1+delta;must(low===195&&high===253,'Hasse bound');
 const hist={};let count=0,max=0;
 for(let m=low;m<=high;m++){let g=gcdEuclid(m,n);hist[g]=(hist[g]||0)+1;count++;max=Math.max(max,g);must(g===1||g===2||g===4,'odd common factor')}
 must(max===4&&count===59,'unexpected Hasse scan');
 return {schema:'ct165-abstract-group-obstruction/v1',base_field:p,actual_fixed_nu12_order:n,odd_prime_factor:r,odd_factor_prime_trial_certified:true,hasse_order_interval:[low,high],possible_order_integers_checked:count,gcd_histogram:Object.fromEntries(Object.entries(hist).sort((a,b)=>+a[0]-+b[0])),maximum_possible_image_order:max,maximum_possible_odd_image_order:1,fixed_quotient_kernels_bound:y.length,theorem_scope:'every abstract group hom E(F223)->B(F223), B/F223 F223-isogenous to CT160 Weil restriction',consequence:'no injective scalar-preserving transfer on any odd-prime-order E(F223) subgroup',standing:'[pcc:unverified]; arithmetic source audit, no signed PCC or ECDLP speedup'};
}
const base=verify(A);
const negs=[
 ['source_order',x=>x.census.actual_fixed_nu12_source.order++],
 ['census_count',x=>x.census.actual_fixed_nu12_target.zeros=5],
 ['wrong_generator',x=>x.audit.model_generators[0].generator_prime_order=211],
 ['wrong_kernels',x=>x.kernels.kernels.pop()],
 ['wrong_quotient_order',x=>x.quotients.full_curve_order=11086842],
 ['wrong_basis',x=>x.quotients.kernels[0].basis=[2,8,32]],
 ['counter_as_bool',x=>x.audit.model_generators[0].group_order=true],
];
const rejected=[];
for(const [name,mutation] of negs){const x=structuredClone(A);mutation(x);try{verify(x);throw new Error('mutation falsely accepted: '+name)}catch(e){if(e.message.startsWith('mutation falsely accepted:'))throw e;rejected.push(name)}}
base.negative_controls_rejected=rejected;
function canonical(o){if(Array.isArray(o))return '['+o.map(canonical).join(',')+']';if(o&&typeof o==='object')return '{'+Object.keys(o).sort().map(k=>JSON.stringify(k)+':'+canonical(o[k])).join(',')+'}';return JSON.stringify(o)}
console.log(canonical(base));
