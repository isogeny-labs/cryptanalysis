//! Native qualification only. Solver invocation is a separately registered job.
use num_bigint::BigUint;
use serde_json::{json, Value};
use std::{
    env, fs,
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};
use torus_s4::{curve25519_prime, decimal, sha256, Case, Curve, System};
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
fn save(path: impl AsRef<Path>, v: &Value) -> Result<()> {
    fs::write(path, serde_json::to_vec_pretty(v)?)?;
    Ok(())
}
fn hash_file(p: impl AsRef<Path>) -> Result<String> {
    Ok(sha256(&fs::read(p)?))
}
fn freeze(dir: &Path) -> Result<()> {
    fs::create_dir(dir)?;
    let exe = env::current_exe()?;
    let target = dir.join("qualifier");
    fs::copy(&exe, &target)?;
    let mut permissions = fs::metadata(&target)?.permissions();
    permissions.set_readonly(true);
    fs::set_permissions(&target, permissions)?;
    save(
        dir.join("qualifier.json"),
        &json!({"schema":"torus-s4.qualifier/v1","binary_sha256":hash_file(&target)?,"binary":"qualifier","role":"development-correctness-qualification","execution_verified":false}),
    )?;
    Ok(())
}
fn immutable_qualifier() -> Result<String> {
    let exe = env::current_exe()?;
    let pin: Value = serde_json::from_slice(&fs::read(
        exe.parent()
            .ok_or("missing executable directory")?
            .join("qualifier.json"),
    )?)?;
    let hash = hash_file(&exe)?;
    if pin["binary_sha256"] != hash || !fs::metadata(&exe)?.permissions().readonly() {
        return Err("run the immutable binary created by freeze".into());
    }
    Ok(hash)
}
fn triple(v: &Value) -> Result<[BigUint; 3]> {
    let a = v.as_array().ok_or("triple must be an array")?;
    if a.len() != 3 {
        return Err("expected three u coordinates".into());
    }
    let mut r = vec![];
    for x in a {
        r.push(decimal(
            x.as_str().ok_or("u coordinates must be decimal strings")?,
        )?);
    }
    Ok(r.try_into().map_err(|_| "expected triple")?)
}
fn safe_stem(p: &Path) -> Result<String> {
    let s = p
        .file_stem()
        .and_then(|v| v.to_str())
        .ok_or("invalid input filename")?;
    if s.is_empty() || !s.chars().all(|c| c.is_ascii_alphanumeric() || c == '_') {
        return Err("unsafe input filename".into());
    }
    Ok(s.into())
}
fn qualify(cases: &Path, known: &Path, out: &Path) -> Result<()> {
    let binary = immutable_qualifier()?;
    let mut paths: Vec<PathBuf> = fs::read_dir(cases)?
        .map(|e| e.map(|e| e.path()))
        .collect::<std::io::Result<_>>()?;
    paths.retain(|p| p.extension().is_some_and(|x| x == "json"));
    paths.sort();
    if paths.is_empty() {
        return Err("no input cases".into());
    }
    let mut inputs = vec![];
    for p in &paths {
        inputs.push(json!({"file":safe_stem(p)?,"sha256":hash_file(p)?}));
    }
    let known_bytes = fs::read(known)?;
    fs::create_dir(out)?;
    // This manifest precedes compilation and parsing the known-answer labels.
    save(
        out.join("qualification-pre-call.json"),
        &json!({"schema":"torus-s4.qualification-pre-call/v1","binary_sha256":binary,"inputs":inputs,"known_answers_sha256":sha256(&known_bytes),"epoch_seconds":SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs(),"purpose":"correctness qualification; no solver measurement"}),
    )?;
    let mut compiled = vec![];
    for path in &paths {
        let c: Case = serde_json::from_slice(&fs::read(path)?)?;
        if c.field()?.p != curve25519_prime() {
            return Err("this registration requires actual Curve25519 p".into());
        }
        if c.coefficient()? != BigUint::from(486662u32) {
            return Err("this registration requires Curve25519 A=486662".into());
        }
        if c.order()? != 1 && c.order()? != 25606137078333158825u128 {
            return Err("unregistered torus order".into());
        }
        let s = System::compile(&c)?;
        let name = safe_stem(path)?;
        let dir = out.join(&name);
        fs::create_dir(&dir)?;
        let payload = serde_json::to_vec_pretty(&s.canonical_json())?;
        fs::write(dir.join("system.json"), &payload)?;
        fs::write(dir.join("input.sing"), s.singular())?;
        // Case serialization removes the historical `kind` hint; no generation labels.
        fs::write(dir.join("case.json"), serde_json::to_vec_pretty(&c)?)?;
        compiled.push((c, s, name, sha256(&payload)));
    }
    let answers: Value = serde_json::from_slice(&known_bytes)?;
    let mut rows = vec![];
    for (c, s, name, hash) in compiled {
        let mut checked = 0;
        if let Some(list) = answers.get(&c.id) {
            for v in list.as_array().ok_or("expected list of triples")? {
                let us = triple(v)?;
                s.check(&s.witness(&c, &us)?)?;
                Curve::from_case(&c)?.verify_triple(&c, &us)?;
                checked += 1;
            }
        }
        rows.push(json!({"case":name,"p_bits":s.p.bits(),"M":c.m.to_string(),"variables":s.variables.len(),"equations":s.equations.len(),"max_degree":s.equations.iter().map(|p|p.degree()).max(),"system_sha256":hash,"known_triples_checked":checked,"solver_invoked":false,"absence_certified":false}));
    }
    save(
        out.join("qualification-post-call.json"),
        &json!({"schema":"torus-s4.qualification-post-call/v1","pre_call_sha256":hash_file(out.join("qualification-pre-call.json"))?,"cases":rows,"pcc_standing":"unverified","phase":"correctness qualification"}),
    )?;
    println!("{}", out.join("qualification-post-call.json").display());
    Ok(())
}
fn check(case: &Path, candidates: &Path) -> Result<()> {
    let c: Case = serde_json::from_slice(&fs::read(case)?)?;
    c.validate()?;
    let v: Value = serde_json::from_slice(&fs::read(candidates)?)?;
    let us = triple(&v)?;
    let curve = Curve::from_case(&c)?;
    let signs = curve.verify_triple(&c, &us)?;
    let s = System::compile(&c)?;
    s.check(&s.witness(&c, &us)?)?;
    println!(
        "{}",
        json!({"point_sum_check":"producer_pass","negative_signs":signs,"pcc_standing":"unverified"})
    );
    Ok(())
}
fn run() -> Result<()> {
    let a: Vec<_> = env::args().collect();
    match a.get(1).map(String::as_str){
        Some("freeze") if a.len()==3=>freeze(Path::new(&a[2])),
        Some("qualify") if a.len()==5=>qualify(Path::new(&a[2]),Path::new(&a[3]),Path::new(&a[4])),
        Some("check") if a.len()==4=>check(Path::new(&a[2]),Path::new(&a[3])),
        _=>Err("usage: qualifier freeze NEW_DIR | qualify CASES KNOWN.json NEW_OUTPUT_DIR | check CASE.json TRIPLE.json".into())
    }
}
fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_bad_candidate_shape() {
        assert!(triple(&json!(["1", "2"])).is_err());
        assert!(triple(&json!([1, 2, 3])).is_err());
        assert!(triple(&json!(["1", "2", "-3"])).is_err());
    }
    #[test]
    fn rejects_unsafe_names() {
        assert!(safe_stem(Path::new("../escape.json")).is_ok());
        assert!(safe_stem(Path::new("a.b.json")).is_err());
        assert!(safe_stem(Path::new(".json")).is_err());
    }
}
