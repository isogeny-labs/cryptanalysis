"""Author additive source files and literal rewrites; no research arithmetic."""
from pathlib import Path
import hashlib,json,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';old=s/'fixed-jacobian-chain-evaluator-01';p=s/'fixed-jacobian-chain-evaluator-02';p.mkdir();(p/'src/bin').mkdir(parents=True);(p/'lean').mkdir()
(p/'.gitignore').write_text('/generated/\n/derived/\n')
body=(old/'Cargo.toml').read_text().replace('name = "chained-n4-fixed-jacobian-chain-evaluator"','name = "chained-n4-fixed-jacobian-chain-norm-reuse"').replace('name = "audit-fixed-jacobian-chain"','name = "audit-norm-point-reuse"').replace('[workspace]','[[bin]]\nname = "derive-norm-point-expected"\npath = "src/bin/derive_expected.rs"\n\n[lib]\npath = "derived/lib.rs"\n\n[workspace]')
(p/'Cargo.toml').write_text(body)
lock=(old/'Cargo.lock').read_text();assert lock.count('name = "chained-n4-fixed-jacobian-chain-evaluator"')==1;(p/'Cargo.lock').write_text(lock.replace('name = "chained-n4-fixed-jacobian-chain-evaluator"','name = "chained-n4-fixed-jacobian-chain-norm-reuse"'))
for a,b in [('materialize.py','materialize-helpers.py'),('capture_engine.py','capture_engine.py'),('runtime_custody.py','runtime_custody.py'),('src/bin/audit_chain.rs','src/bin/audit_chain.rs')]:shutil.copyfile(old/a,p/b)
cap=(old/'capture_auditor.py').read_text().replace("=='audit-fixed-jacobian-chain'","==sys.argv[3]").replace("out/'actual-compiled-auditor.bin'","out/('actual-compiled-'+sys.argv[3]+'.bin')").replace("out/'auditor-actual-path.txt'","out/(sys.argv[3]+'-actual-path.txt')").replace("('auditor-'+mode+'-custody.json')","(sys.argv[3]+'-'+mode+'-custody.json')")
(p/'capture_executable.py').write_text(cap)
materializer=r"""# Exact literal source derivative under published25d29e; no arithmetic.
from pathlib import Path
import hashlib,json,subprocess,sys
p=Path(__file__).resolve().parent
old=p.parent/'fixed-jacobian-chain-evaluator-01'
assert not (p/'generated').exists() and not (p/'derived').exists()
subprocess.run([sys.executable,str(p/'materialize-helpers.py')],check=True)
d=p/'derived';d.mkdir()
rows=[]
for name in ['lib.rs','rational.rs','tests.rs']:
 source=old/'src'/name;b=source.read_bytes();(d/name).write_bytes(b)
 rows.append(dict(source=str(source.relative_to(p.parent)),sha256=hashlib.sha256(b).hexdigest(),destination='derived/'+name,explicit_changes=[]))
lib=(d/'lib.rs').read_text()
patches=[
('    pub degree169_elliptic_evaluation: u64,','    pub degree169_elliptic_evaluation: u64,\n    pub transported_norm_doubling: u64,'),
('    pub fn transfer_entry(&self, input: &Entry, to: usize) -> Result<Entry> {',
'''    fn norm_point(&self, to: usize, point: Pt<ER>) -> Pt<ER> {
        self.bump(|c| c.transported_norm_doubling += 1);
        let target = &self.geometry.models[to].quadratic;
        descend_point(curve::pmul(&target.f, &target.curve, &point, 2))
    }
    pub fn transfer_entry(&self, input: &Entry, to: usize) -> Result<Entry> {'''),
('''        let class = self.target_phi(to, self.gamma(input.domain, to, lifted)?)?;
        let norm = descend_point(self.gamma(input.domain, to, lift(input.norm))?);''',
'''        let point = self.gamma(input.domain, to, lifted)?;
        let class = self.target_phi(to, point)?;
        let norm = self.norm_point(to, point);'''),
('''        let norm =
            descend_point(self.gamma(1, to, self.gamma(input.domain, 1, lift(input.norm))?)?);''',
'''        let norm = self.norm_point(to, point);'''),
('''        let corrected_class = self.target_phi(to, self.gamma(from, to, lifted)?)?;''',
'''        let point = self.gamma(from, to, lifted)?;
        let corrected_class = self.target_phi(to, point)?;'''),
('''        let norm = descend_point(self.gamma(from, to, lift(input.norm))?);''',
'''        let norm = self.norm_point(to, point);''')]
for before,after in patches:
 assert lib.count(before)==1,before
 lib=lib.replace(before,after)
 rows[0]['explicit_changes'].append(dict(before=before,after=after,occurrences=1))
(d/'lib.rs').write_text(lib)
(p/'generated/source-derivative-custody.json').write_text(json.dumps(dict(protocol='25d29e published67a90fd7 before code',literal_source_members=rows,scope='Only the six declared source replacements; rational composition and entire unfiltered test body literal unchanged.'),indent=2)+'\n')
print('Literal baseline source copied; six declared norm-point/counter replacements; tests and rational module unchanged')
"""
(p/'materialize.py').write_text(materializer)
# Pin all original frozen inputs plus every tracked immutable baseline member.
refs={n:h for h,n in (line.split('  ',1)for line in (old/'frozen-prior-inputs-01.sha256').read_text().splitlines())}
import subprocess
for name in subprocess.check_output(['git','ls-files',str(old.relative_to(r))],cwd=r,text=True).splitlines():
 q=r/name
 if q.is_file():refs[name]=hashlib.sha256(q.read_bytes()).hexdigest()
(p/'frozen-prior-inputs-01.sha256').write_text(''.join(h+'  '+n+'\n'for n,h in sorted(refs.items())))
(p/'README.md').write_text('''# Norm-point reuse, additive evaluator02\n\nProtocol25d29e was published at67a90fd7 before this source. materialize.py copies the whole frozen evaluator01 lib/tests/rational modules; materialize-helpers.py is the literal original helper copier. Six explicit guarded replacements add one counter, retain the final elliptic point, and double it for the norm in direct, retained-lift and full-half diagnostic routes. No original source, model, field, kernel, sign, test population or arithmetic body is changed. [pcc:unverified]\n\nThe original dual identity N(Phi(Z))=[2]Z motivates the optimization. The new Lean module records its conditional algebraic bridge and derivation from half/correction and map linearity. Actual native descent/norm/inverse and independent original elliptic checks remain mandatory. Mathematical validity of the full encoded program is still conditional on the existing geometric/program bridges. [pcc:unverified]\n\nThe Rust expected-fixture derivation pins the original whole123,633,074B fixture by SHA-256, requires all695 ordered records and exactly the48 selected vectors and their complete counter schema, and makes only the published2-to1/4-to2 evaluation changes plus new1/2/1 doubling counters. The literal original whole-record auditor compares all records; all four entire-record-class omissions must reject101 without output. Full native has not yet run. [pcc:unverified]\n\nOne900s engine preparation on the declared warm cache,120s wrappers and one900s/2GiB unfiltered native attempt per published compiled source; original exact checkpoint and immediate gate are required. Preserve every source/compiler/runtime/prepared-library byte and failed attempt for NEW23. Selected calls are unpriced; complete setup/reuse primitive accounting and the stronger public-known-initial-lift ECDLP comparator remain open. No calibrated speed, ECDLP advantage or signed standing is inferred. [pcc:unverified]\n''')
print(p, len(refs))
