"""Literal observer insertions and exact reverse restoration, no research arithmetic."""
from pathlib import Path
import hashlib,json,re,sys
root,out=map(Path,sys.argv[1:]);audit=Path(__file__).resolve().parent
study='cryptanalysis/experiments/chained-transfer-public-target/'
qpath=study+'beta-rational-lift/quadratic-picard-engine/src/lib.rs'
changes=[];originals={}
def replace(path,old,new,label):
 p=root/path;text=p.read_text();originals.setdefault(path,text);assert text.count(old)==1,(path,label,text.count(old));p.write_text(text.replace(old,new));changes.append({'path':path,'label':label,'old':old,'new':new})
def hits(backend,modulus,ops):
 return ''.join(f'        n4_arithmetic_taps::hit("{backend}", {modulus}, "{op}", {n});\n'for op,n in ops)
coef='quadratic.Picard.coefficient';enc='quadratic.Picard.encoding';prime='quadratic.Picard.prime'
old='    fn mulu(&self, a: u32, b: u32) -> u32 {\n        if let Some(nu) = self.quadratic_nu {\n';replace(qpath,old,old+hits(coef,'self.q',[('mul',5),('add',2),('rem_u64',2)])+hits(enc,'self.q',[('decode_rem',2),('decode_div',2),('pack_mul',1),('pack_add',1)]),'quadratic multiplication: five written coefficient products')
old='        ((a as u64 * b as u64) % self.q) as u32\n';replace(qpath,old,hits(prime,'self.q',[('mul',1),('rem_u64',1)])+old,'nondelegating prime multiplication')
old='    fn add_nc(&self, a: u32, b: u32) -> u32 {\n        if self.quadratic_nu.is_some() {\n';replace(qpath,old,old+hits(coef,'self.q',[('add',2),('rem_u64',2)])+hits(enc,'self.q',[('decode_rem',2),('decode_div',2),('pack_mul',1),('pack_add',1)]),'quadratic addition')
old='        let s = a as u64 + b as u64;\n';replace(qpath,old,hits(prime,'self.q',[('add',1)])+old,'prime addition')
old='    fn sub_nc(&self, a: u32, b: u32) -> u32 {\n        if self.quadratic_nu.is_some() {\n';replace(qpath,old,old+hits(coef,'self.q',[('sub',2),('rem_u64',2)])+hits(enc,'self.q',[('decode_rem',2),('decode_div',2),('pack_mul',1),('pack_add',1),('modulus_adjust_add',2)]),'quadratic subtraction')
old='        if a >= b {\n            a - b\n';replace(qpath,old,hits(prime,'self.q',[('sub',1)])+old,'prime subtraction')
old='        if a == 0 {\n            0\n        } else {\n            (self.q - a as u64) as u32\n';replace(qpath,old,'        if a != 0 { n4_arithmetic_taps::hit("quadratic.Picard.prime", self.q, "neg", 1); }\n'+old,'nonzero prime negation; quadratic branch delegates')
old='    fn invu(&self, a: u32) -> u32 {\n        if let Some(nu) = self.quadratic_nu {\n';replace(qpath,old,old+hits(coef,'self.q',[('sq',1),('mul',4),('sub',2),('rem_u64',4)])+hits(enc,'self.q',[('decode_rem',1),('decode_div',1),('pack_mul',1),('pack_add',1),('modulus_adjust_add',1)]),'quadratic inverse scaling; base inverse counted at delegated leaf')
old='    fn base_invu(&self, a: u32) -> u32 {\n';replace(qpath,old,old+hits(prime,'self.q',[('inv',1)]),'atomic Euclidean base inverse, internals unpriced')
old='        a % p + p * ((p - a / p) % p)\n';replace(qpath,old,hits(coef,'self.fq.q',[('sub',1),('rem_u64',1)])+hits(enc,'self.fq.q',[('decode_rem',1),('decode_div',1),('pack_mul',1),('pack_add',1)])+old,'actual coefficient Frobenius')
old='    while d * d <= q {\n        if q.is_multiple_of(d) {\n';replace(qpath,old,'    while d * d <= q {\n'+hits('quadratic.Picard.primality.aux','q',[('trial_divisibility',1)])+'        if q.is_multiple_of(d) {\n','constructor integer trial divisions')
# Reuse the original already audited prime-polynomial hooks on an identical body.
marker='/// First rational point in the canonical order'
untouched=(root.parent/'original-layout/crypto/src/cryptanalysis/plane_quartic_pic.rs').read_text();patched=(root/'crypto/src/cryptanalysis/plane_quartic_pic.rs').read_text();current=(root/qpath).read_text()
def block(text):return text[text.index('fn pmod_mul('):text.index(marker)]
a,b,c=map(block,[untouched,patched,current]);assert a==c,'copied prime helper body differs; inspect rather than guess'
without='\n'.join(line for line in b.splitlines()if'n4_arithmetic_taps::hit'not in line)
assert ''.join(without.split())==''.join(a.split()),'original polynomial hook arithmetic tokens changed'
b=b.replace('"Picard.polynomial"','"quadratic.Picard.polynomial"').replace('"Picard.point_search"','"quadratic.Picard.point_search"')
replace(qpath,a,b,'unchanged original prime-polynomial and point-search hook block')
# Record uncovered random-residue bookkeeping explicitly as auxiliary work.
for old,modulus,label in [('            let a = xorshift_next(rng) % q;\n','q','polynomial random residue'),('        let y = xorshift_next(rng) % qq;\n','qq','point search random residue'),('            *c = (xorshift_next(rng) % q as u64) as u32;\n','q as u64','random curve coefficient residue')]:
 replace(qpath,old,hits('quadratic.Picard.random.aux',modulus,[('rng_residue',1)])+old,label)
# Add only diagnostic entries at delegated APIs, never additional primitive work.
for name,args in [('mul','a: u32, b: u32'),('add','a: u32, b: u32'),('sub','a: u32, b: u32'),('neg','a: u32'),('inv','a: u32'),('invu','a: u32')]:
 old=f'    fn {name}(&self, {args}) -> u32 {{\n';replace(qpath,old,old+hits('quadratic.Picard.api','self.q',[(name,1)]),'delegating API '+name)
# Public field-count test access exists only in the separate audit derivative.
control=(audit/'quadratic_controls.rs').read_text();replace(qpath,'\n'+marker,'\n'+marker,'anchor check')
q=root/qpath;old=q.read_text();append='\n// Additive derivative-only control access; original arithmetic prefix is unchanged.\n'+control;q.write_text(old+append);changes.append({'path':qpath,'label':'test-only quadratic control access','old':'','new':append,'append':True})
qcargo=study+'beta-rational-lift/quadratic-picard-engine/Cargo.toml';p=root/qcargo;originals[qcargo]=p.read_text();added='''
[features]
arithmetic-audit-controls = ["dep:isogeny_algos"]
[dependencies]
n4-arithmetic-taps = { path = "../../../../../n4-arithmetic-taps" }
serde_json = "=1.0.145"
isogeny_algos = { path = "../../../../../crypto/isogeny_algos", optional = true }
''';p.write_text(p.read_text()+added);changes.append({'path':qcargo,'label':'observer/control dependencies','old':'','new':added,'append':True})
# The norm wrapper gets only observer access and phase markers.
ncargo=study+'norm-halving-evaluator/Cargo.toml';replace(ncargo,'[dependencies]\n','[dependencies]\nn4-arithmetic-taps = { path = "../../../../n4-arithmetic-taps" }\n','observer dependency')
phases=[(study+'norm-halving-evaluator/src/lib.rs','    fn evaluate(\n','        let (x, norm) = self.admit(side, field, model, key)?;\n','strong.transfer'),(study+'norm-halving-evaluator/src/direct.rs','    fn evaluate(&self, side: usize, field: &str, model: &str, key: &[u32; 19]) -> Result<PicClass> {\n',None,'direct.transfer'),(study+'norm-halving-evaluator/src/direct.rs','    pub fn halves_of_norm(&self, side: usize, norm: Pt<ER>) -> Result<Vec<Pt<ER>>> {\n',None,'halving'),(study+'norm-halving-evaluator/src/direct.rs','pub fn generic_half(f: &FpR, e: &Curve<ER>, q: Pt<ER>, x: ER) -> Result<Pt<ER>> {\n',None,'half.ordinate')]
for path,anchor,line,label in phases:
 if line:replace(path,line,'        let _arithmetic_phase = n4_arithmetic_taps::phase("'+label+'");\n'+line,label)
 else:replace(path,anchor,anchor+'        let _arithmetic_phase = n4_arithmetic_taps::phase("'+label+'");\n',label)
# Preserve input norm/order separation even when old leaf scope names override scope().
path=study+'norm-halving-evaluator/src/lib.rs';old='    let q = if side == 0 {\n        ep(old.norm(&x)?)\n    } else {\n        ep(new.norm(&x)?)\n    };\n';new='    let q = { let _arithmetic_phase = n4_arithmetic_taps::phase("input.norm");\n'+old.replace('    let q = ','',1).removesuffix(';\n')+' };\n';replace(path,old,new,'common full input norm')
old='    if !pic.is_zero(&pic.mul_scalar(&x, ORDER as u128)) {\n        return Err("class outside the written rational group order".into());\n    }\n';replace(path,old,'    { let _arithmetic_phase = n4_arithmetic_taps::phase("input.order");\n'+old+'    }\n','common full group order admission')
# The baseline full inverse is exactly its existing value-level dual plus the
# original Jacobian scalar; it adds no intermediate decoder/norm admission.
path=study+'norm-halving-evaluator/src/lib.rs';p=root/path;before=p.read_text();addition='\nimpl StrongScalarBaseline {\n    pub fn arithmetic_audit_full_inverse(&self, packet: &NewPacket) -> Result<OldPacket> {\n        let _arithmetic_phase=n4_arithmetic_taps::phase("full.inverse");\n        let y=self.evaluate(1,&packet.field,&packet.model,&packet.key,true)?;\n        Ok(self.reference.old().encode(&self.reference.old().a.pic.mul_scalar(&y,3413013)))\n    }\n}\n'
p.write_text(before+addition);changes.append({'path':path,'label':'value-level strongest baseline full inverse, declared protocol composition','old':'','new':addition,'append':True})
path=study+'norm-halving-evaluator/src/direct.rs';old='    pub fn inverse(&self, p: &NewPacket) -> Result<OldPacket> {\n';replace(path,old,old+'        let _arithmetic_phase = n4_arithmetic_taps::phase("full.inverse");\n','direct full inverse phase')
# Reverse every new edit exactly; old patch restoration remains independently pinned.
for path,before in originals.items():
 restored=(root/path).read_text()
 for change in reversed([row for row in changes if row['path']==path]):
  if change.get('append'):
   assert restored.endswith(change['new']);restored=restored[:-len(change['new'])]
  else:
   assert restored.count(change['new'])==1,(path,change['label']);restored=restored.replace(change['new'],change['old'])
 assert restored==before,path
inventory=[{'path':path,'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':hashlib.sha256((root/path).read_bytes()).hexdigest(),'new_edits_exactly_reversed':True}for path,before in originals.items()]
(out/'new-literal-changes.json').write_text(json.dumps(changes,indent=2)+'\n');(out/'new-hook-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n');print('new literal edits',len(changes),'all original bodies restored exactly')
