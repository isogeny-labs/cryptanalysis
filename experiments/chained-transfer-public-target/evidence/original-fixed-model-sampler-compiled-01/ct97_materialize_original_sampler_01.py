"""Literal sampler/class-solver adaptation to the already accepted original geometry."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'original-fixed-model-sampler-01';assert not(p/'src/lib.rs').exists()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()=='80631ad65241cbec113ccf1e1d618a076da3a4d7'
p.mkdir(exist_ok=True);(p/'src/bin').mkdir(parents=True,exist_ok=True);(p/'derived').mkdir();(p/'original').mkdir()
old=s/'norm-assisted-ic';baseline=s/'original-fixed-model-ic-01'
shutil.copyfile(old/'derived/class_solver.rs',p/'derived/class_solver.rs');shutil.copyfile(s/'new-target-ic/derived/class_solver.rs',p/'original/class_solver.rs');shutil.copyfile(old/'src/lib.rs',p/'original/sampler.rs')
t=(old/'src/lib.rs').read_text()
changes=[('//! Exact-class sampling; prospective4a6745 published b57b1024 BEFORE code.','//! Original fixed-model sampler under prospectiveabf432 published80631ad before source.'),('use chained_n4_odd_product_maps::{norm::EncodedClass, NormNew, Point};','use chained_n4_original_full_geometry::{norm::EncodedClass, FixedGeometry, NormNew, Point};'),('use chained_n4_odd_product_models::{er, three};','use chained_n4_paired_fourth_preflight::models::{er, three};'),("pub fn new(norm: &'a NormNew, generator: &EncodedClass) -> Result<Self, String> {","pub fn new(geometry: &'a FixedGeometry, side: usize, generator: &EncodedClass) -> Result<Self, String> {"),('chained_n4_new_target_ic::TargetContext::new(norm)?;','chained_n4_original_fixed_model_ic::TargetContext::new(geometry, side)?;\n        let norm = &geometry.models[side].prime;')]
for a,b in changes:assert t.count(a)==1,a;t=t.replace(a,b,1)
(p/'src/lib.rs').write_text(t)
for name in ['inherit_prepared.py','capture_binary.py','capture_engine.py','runtime_custody.py']:shutil.copyfile(baseline/name,p/name)
t=(baseline/'build-only-01.sh').read_text().replace('chained_n4_original_fixed_model_ic','chained_n4_original_fixed_model_sampler').replace('audit-original-fixed-model-ic','audit-original-fixed-model-sampler');(p/'build-only-01.sh').write_text(t)
shutil.copyfile(s/'evidence/original-fixed-model-sampler-prospective-01/frozen-before-sampler-source.sha256',p/'frozen-prior-inputs-01.sha256')
(p/'.gitattributes').write_text('derived/class_solver.rs -whitespace\noriginal/class_solver.rs -whitespace\noriginal/sampler.rs -whitespace\n')
(p/'literal-source-provenance.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),prospective='abf432/80631ad BEFOREsource',old_sampler='9bc5e6',accepted_fixed_baseline='7df2ae/ba1fae2',old_sampler_class_body_wholebytes_equal=True,whole_candidate_sha256=hashlib.file_digest((p/'derived/class_solver.rs').open('rb'),'sha256').hexdigest(),whole_baseline_sha256=hashlib.file_digest((p/'original/class_solver.rs').open('rb'),'sha256').hexdigest(),surrounding_source_literal_replacements=changes,all_other_sampler_library_bytes_unchanged_before_formatting=True,strong_reference='derived public generator source will be compared with already known independently transported generator; no outcome inferred',scope='mechanical source/type adaptation only; no native result or cost claim'),indent=2)+'\n')
shutil.copyfile(__file__,p/'materialize-support.py');print('literal sampler installed under publishedprospective',flush=True)
