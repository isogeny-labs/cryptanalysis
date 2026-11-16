# Exact literal source derivative under published25d29e; no arithmetic.
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
