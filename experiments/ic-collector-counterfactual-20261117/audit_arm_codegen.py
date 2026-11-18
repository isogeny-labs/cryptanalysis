#!/usr/bin/env python3
"""Audit identical real Gf2 bodies under generic/aes compilation; no timings."""
import hashlib,json,os,platform,re,signal,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];D=P/'arm-codegen-001';D.mkdir(exist_ok=False)
assert platform.machine()=='arm64'
source=ROOT/'suite/src/cryptanalysis/semaev_decomp.rs';raw=source.read_text();sha=lambda b:hashlib.sha256(b).hexdigest()
start=raw.index('#[derive(Debug)]\nstruct Gf2Tables');end=raw.index('// ── Polynomials over',start)
body=raw[start:end];cut=body.index('    /// Lift to the crate\'s general element type.')
body=body[:cut]+'}\n'
fields=json.loads((P/'instances.json').read_text())
cases=',\n'.join('IrreduciblePoly { degree: '+str(x['field']['degree'])+', low_terms: vec!['+','.join(str(e) for e in x['field']['modulus_exponents'] if e!=x['field']['degree'])+'] }' for x in fields)
pre='use std::collections::HashMap;\n#[derive(Clone)] pub struct IrreduciblePoly { pub degree:u32, pub low_terms:Vec<u32> }\n'
post=r'''
#[no_mangle]
#[inline(never)]
pub fn baseline_body(gf:&Gf2,xs:&mut[u64],scratch:&mut Vec<u64>){gf.batch_inv_body(xs,scratch)}
#[no_mangle]
#[inline(never)]
#[target_feature(enable="aes")]
pub unsafe fn aes_body(gf:&Gf2,xs:&mut[u64],scratch:&mut Vec<u64>){gf.batch_inv_body(xs,scratch)}
fn reference_mul(a:u64,b:u64,n:u32,irr:u64)->u64{
 let mut w=0u128;
 for bit in 0..64 {if (b>>bit)&1!=0 {w^=(a as u128)<<bit;}}
 for bit in (n..128).rev() {if (w>>bit)&1!=0 {w^=(irr as u128)<<(bit-n);}}
 w as u64
}
fn main(){
 assert!(std::arch::is_aarch64_feature_detected!("aes"));
 let cases=vec![__CASES__];let mut checked=0usize;let mut seed=0x18abde129fab381u64;
 for irr in cases {
  let gf=Gf2::new(&irr);assert!(gf.has_clmul());
  for len in (0..=17).chain([63,64,65,1024,1027]) {
   let input:Vec<u64>=(0..len).map(|i|{seed^=seed<<13;seed^=seed>>7;seed^=seed<<17;if i%7==3{0}else{seed&gf.mask}}).collect();
   let mut left=input.clone();let mut right=input.clone();
   baseline_body(std::hint::black_box(&gf),&mut left,&mut Vec::new());
   // SAFETY: runtime aes detection succeeded before any enabled wrapper call.
   unsafe{aes_body(std::hint::black_box(&gf),&mut right,&mut Vec::new())};
   assert_eq!(left,right);
   for (&x,&inverse) in input.iter().zip(&left){
    if x==0{assert_eq!(inverse,0)}else{assert_eq!(reference_mul(x,inverse,gf.n,gf.irr),1)}
    checked+=1;
   }
  }
 }
 println!("{{\"status\":\"pass\",\"fields\":5,\"checked_elements\":{},\"timing\":false}}",checked);
}
'''.replace('__CASES__',cases)
(D/'audit.rs').write_text(pre+body+post)
commands=[]
def run(argv,name,cap):
 proc=subprocess.Popen(argv,cwd=D,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,text=True)
 try:out,err=proc.communicate(timeout=cap);code=proc.returncode
 except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);out,err=proc.communicate();code=124
 (D/(name+'.stdout')).write_text(out);(D/(name+'.stderr')).write_text(err);commands.append(dict(argv=argv,exit_code=code,cap_seconds=cap));assert code==0,name
 return out
receipt=dict(status='started',scope='Reduced-scope optimized ARM codegen and arithmetic correctness; not full-crate or performance validation',source_sha256=sha(source.read_bytes()),extracted_body_sha256=sha(body.encode()),generated_source_sha256=sha((D/'audit.rs').read_bytes()),platform=platform.platform(),commands=commands)
try:
 receipt['rustc']=subprocess.check_output(['rustc','-Vv'],text=True)
 run(['rustc','--edition=2021','-C','opt-level=3','-C','codegen-units=1','-C','panic=abort','--emit=asm,link','audit.rs','-o','audit'],'compile',60)
 receipt['correctness']=json.loads(run([str((D/'audit').resolve())],'unit',30))
 asm=(D/'audit.s').read_text();rows={}
 for name in ['baseline_body','aes_body']:
  match=re.search(r'^_'+name+r':\n(.*?)(?=^Lfunc_end|^\s*\.globl|\Z)',asm,re.M|re.S);assert match,name
  text=match.group(1);calls=re.findall(r'^\s*(?:bl|b)\s+([^\n]+)',text,re.M)
  rows[name]=dict(pmull_instructions=len(re.findall(r'\bpmull2?\b',text)),direct_clmul_neon_calls=sum('clmul_u64_neon' in c for c in calls),calls=calls)
 receipt['bodies']=rows;receipt['assembly_sha256']=sha((D/'audit.s').read_bytes());receipt['binary_sha256']=sha((D/'audit').read_bytes());receipt['production_source_unchanged']=sha(source.read_bytes())==receipt['source_sha256'];assert receipt['production_source_unchanged']
 receipt['status']='pass'
except Exception as e:receipt.update(status='failed_or_capped',error=repr(e));raise
finally:(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
