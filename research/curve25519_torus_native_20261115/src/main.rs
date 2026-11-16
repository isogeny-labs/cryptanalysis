//! Native qualification and bounded root recovery. Solver trials are separately registered.
mod recovery;
mod tree_recovery;
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
fn prepare_engine(case: &Path, out: &Path) -> Result<()> {
    let binary = immutable_qualifier()?;
    let input = fs::read(case)?;
    let c: Case = serde_json::from_slice(&input)?;
    fs::create_dir(out)?;
    save(
        out.join("engine-preparation-pre-call.json"),
        &json!({"schema":"torus-s4.engine-preparation/v1","binary_sha256":binary,"case_sha256":sha256(&input),"purpose":"native basis serialization; no solver invoked"}),
    )?;
    let s = System::compile(&c)?;
    fs::write(out.join("input.sing"), recovery::engine_script(&s)?)?;
    fs::write(out.join("case.json"), serde_json::to_vec_pretty(&c)?)?;
    Ok(())
}
fn recover(case: &Path, transcript: &Path, out: &Path) -> Result<()> {
    let binary = immutable_qualifier()?;
    let input = fs::read(case)?;
    let raw = fs::read(transcript)?;
    fs::create_dir(out)?;
    save(
        out.join("recovery-pre-call.json"),
        &json!({"schema":"torus-s4.recovery-pre-call/v1","binary_sha256":binary,"case_sha256":sha256(&input),"transcript_sha256":sha256(&raw),"max_degree":4096,"coefficient_loop_limit":10000000,"branch_limit":4096,"split_attempts":128}),
    )?;
    let c: Case = serde_json::from_slice(&input)?;
    let s = System::compile(&c)?;
    let b = recovery::parse_basis(std::str::from_utf8(&raw)?, s.variables.len(), &c.field()?)?;
    let mut limits = recovery::Limits::default();
    let (count, triples) = recovery::checked_triples(&c, &s, &b, &mut limits)?;
    save(
        out.join("recovery-post-call.json"),
        &json!({"schema":"torus-s4.recovery-post-call/v1","pre_call_sha256":hash_file(out.join("recovery-pre-call.json"))?,"engine_reported_unit":b.engine_reported_unit,"basis_assignments":count,"u_triples":triples.iter().map(|v|v.iter().map(ToString::to_string).collect::<Vec<_>>()).collect::<Vec<_>>(),"coefficient_loop_units":limits.work,"branches":limits.branches,"absence_certified":false,"pcc_standing":"unverified"}),
    )?;
    Ok(())
}
fn prepare_tree(input: &Path, out: &Path) -> Result<()> {
    let binary = immutable_qualifier()?;
    let raw = fs::read(input)?;
    let card: torus_s4_tree::TreeInput = serde_json::from_slice(&raw)?;
    fs::create_dir(out)?;
    save(
        out.join("tree-preparation-pre-call.json"),
        &json!({"schema":"torus-s4-tree.preparation/v1","binary_sha256":binary,"input_sha256":sha256(&raw),"purpose":"public-input native basis serialization; no solver invoked"}),
    )?;
    let tree = torus_s4_tree::TreeSystem::compile(&card)?;
    fs::write(out.join("input.json"), raw)?;
    fs::write(
        out.join("input.sing"),
        recovery::engine_script(&tree.system)?,
    )?;
    save(
        out.join("tree-preparation-post-call.json"),
        &json!({"variables":tree.system.variables.len(),"equations":tree.system.equations.len(),"solver_invoked":false,"script_sha256":hash_file(out.join("input.sing"))?,"pcc_standing":"unverified"}),
    )?;
    Ok(())
}
fn recover_tree(input: &Path, transcript: &Path, out: &Path) -> Result<()> {
    let binary = immutable_qualifier()?;
    let raw = fs::read(input)?;
    let log = fs::read(transcript)?;
    fs::create_dir(out)?;
    save(
        out.join("tree-recovery-pre-call.json"),
        &json!({"schema":"torus-s4-tree.recovery/v1","binary_sha256":binary,"input_sha256":sha256(&raw),"transcript_sha256":sha256(&log),"max_degree":4096,"coefficient_loop_limit":10000000,"branch_limit":4096,"split_attempts":128}),
    )?;
    let card: torus_s4_tree::TreeInput = serde_json::from_slice(&raw)?;
    let tree = torus_s4_tree::TreeSystem::compile(&card)?;
    let basis = recovery::parse_basis(
        std::str::from_utf8(&log)?,
        tree.system.variables.len(),
        &card.curve.field()?,
    )?;
    let mut limits = recovery::Limits::default();
    let (count, certs) = tree_recovery::recover_sums(&card, &tree, &basis, &mut limits)?;
    save(
        out.join("tree-recovery-post-call.json"),
        &json!({"schema":"torus-s4-tree.recovery-post-call/v1","pre_call_sha256":hash_file(out.join("tree-recovery-pre-call.json"))?,"engine_reported_unit":basis.engine_reported_unit,"basis_assignments":count,"certificates":certs.iter().map(|c|json!({"u_coordinates":c.us.iter().map(ToString::to_string).collect::<Vec<_>>(),"negative_signs":c.negative})).collect::<Vec<_>>(),"coefficient_loop_units":limits.work,"branches":limits.branches,"absence_certified":false,"pcc_standing":"unverified"}),
    )?;
    Ok(())
}
/// Complete one-coordinate oracle, actual field, four summands. Development
/// only: the M=1 restriction is constructed here and cannot accept full-M jobs.
fn native_tree_controls(engine: &Path, out: &Path) -> Result<()> {
    use std::process::Command;
    let binary = immutable_qualifier()?;
    let f = torus_s4::Field::new(curve25519_prime())?;
    let curve = Curve {
        f: f.clone(),
        a: 486662u32.into(),
    };
    let beta = BigUint::from(17u32);
    // x=2A²/(2u+A)²-1=17 has exactly these two algebraic u candidates.
    let root = f
        .sqrt(&f.mul(&2u32.into(), &f.inv(&f.add(&beta, &1u32.into()))?))?
        .ok_or("M1 square root")?;
    let mut leaves = vec![];
    for sign in [false, true] {
        let d = f.mul(&curve.a, &root);
        let d = if sign { f.sub(&0u32.into(), &d) } else { d };
        let u = f.mul(&f.sub(&d, &curve.a), &f.inv(&2u32.into())?);
        if let Some(v) = f.sqrt(&curve.rhs(&u))? {
            leaves.push(Some((u, v)));
        }
    }
    if leaves.len() != 1 {
        return Err("complete M1 rational base is not a singleton".into());
    }
    let point = leaves[0].clone();
    let mut card = torus_s4_tree::TreeInput::from_points(
        f.p.clone(),
        curve.a.clone(),
        1,
        vec![beta],
        &vec![point.clone(); 4],
    )?;
    fs::create_dir(out)?;
    let mut prepared = vec![];
    for (name, scalar) in [("four_M1_member", 4u64), ("four_M1_nonmember", 5u64)] {
        let target = curve
            .times(&point, scalar)?
            .ok_or("identity control target")?;
        card.curve.target = [target.0.to_string().parse()?, target.1.to_string().parse()?];
        card.curve.id = name.into();
        let dir = out.join(name);
        fs::create_dir(&dir)?;
        fs::write(dir.join("input.json"), serde_json::to_vec_pretty(&card)?)?;
        let tree = torus_s4_tree::TreeSystem::compile(&card)?;
        fs::write(
            dir.join("input.sing"),
            recovery::engine_script(&tree.system)?,
        )?;
        prepared.push((name, card.clone(), tree));
    }
    save(
        out.join("native-tree-pre-call.json"),
        &json!({"schema":"torus-s4-tree.native-controls/v1","purpose":"M1 actual-field functional controls, no performance claim","binary_sha256":binary,"engine_sha256":hash_file(engine)?,"per_process_cpu_seconds":4,"wall_seconds":5,"address_space_bytes":805306368u64,"inputs":prepared.iter().map(|(name,_,_)|Ok(json!({"case":name,"input_sha256":hash_file(out.join(name).join("input.json"))?,"script_sha256":hash_file(out.join(name).join("input.sing"))?}))).collect::<Result<Vec<_>>>()?}),
    )?;
    let mut rows = vec![];
    for (name, card, tree) in prepared {
        let dir = out.join(name);
        let result = Command::new("prlimit")
            .args([
                "--as=805306368",
                "--cpu=4",
                "--",
                "timeout",
                "--kill-after=1s",
                "5s",
            ])
            .arg(engine)
            .arg("-q")
            .arg(dir.join("input.sing"))
            .output()?;
        fs::write(dir.join("stdout.txt"), &result.stdout)?;
        fs::write(dir.join("stderr.txt"), &result.stderr)?;
        save(
            dir.join("exit.json"),
            &json!({"success":result.status.success(),"code":result.status.code()}),
        )?;
        if !result.status.success() {
            return Err(
                format!("native functional control {name} failed; raw output retained").into(),
            );
        }
        let basis = recovery::parse_basis(
            std::str::from_utf8(&result.stdout)?,
            tree.system.variables.len(),
            &f,
        )?;
        let mut limits = recovery::Limits::default();
        let (assignments, certs) = tree_recovery::recover_sums(&card, &tree, &basis, &mut limits)?;
        // Inspect the known finite base only after the native call. All 16
        // signs of its sole rational coordinate form the complete oracle.
        let us = vec![point.as_ref().ok_or("identity base")?.0.clone(); 4];
        let oracle = tree_recovery::verify_sum(&card, &us).ok();
        let matched = match oracle {
            Some(want) => certs.len() == 1 && certs[0].us == want.us,
            None => certs.is_empty(),
        };
        rows.push(json!({"case":name,"basis_assignments":assignments,"checked_sum_count":certs.len(),"engine_reported_unit":basis.engine_reported_unit,"matches_complete_M1_oracle":matched,"absence_certified":false,"coefficient_loop_units":limits.work,"branches":limits.branches}));
        if !matched {
            return Err(
                format!("native functional control {name} differs from complete oracle").into(),
            );
        }
    }
    save(
        out.join("native-tree-post-call.json"),
        &json!({"schema":"torus-s4-tree.native-controls-post/v1","pre_call_sha256":hash_file(out.join("native-tree-pre-call.json"))?,"rows":rows,"pcc_standing":"unverified","absence_certified":false}),
    )?;
    Ok(())
}
/// Actual-field M=1 development controls only; this cannot launch full-M trials.
fn native_controls(cases: &Path, known: &Path, engine: &Path, out: &Path) -> Result<()> {
    use std::process::Command;
    let binary = immutable_qualifier()?;
    let known_bytes = fs::read(known)?;
    fs::create_dir(out)?;
    let mut prepared = vec![];
    for name in ["M1_planted", "M1_nonmember"] {
        let input = fs::read(cases.join(format!("{name}.json")))?;
        let c: Case = serde_json::from_slice(&input)?;
        if c.order()? != 1
            || c.field()?.p != curve25519_prime()
            || c.coefficient()? != BigUint::from(486662u32)
        {
            return Err("native-controls accepts only registered actual-field M1 fixtures".into());
        }
        let s = System::compile(&c)?;
        let script = recovery::engine_script(&s)?;
        let dir = out.join(name);
        fs::create_dir(&dir)?;
        fs::write(dir.join("input.sing"), &script)?;
        prepared.push((name, c, s, sha256(&input), sha256(script.as_bytes())));
    }
    save(
        out.join("native-recovery-pre-call.json"),
        &json!({"schema":"torus-s4.native-recovery-control/v1","purpose":"M1 development correctness only; no performance assertion","binary_sha256":binary,"engine_sha256":hash_file(engine)?,"known_answers_sha256":sha256(&known_bytes),"inputs":prepared.iter().map(|(name,_,_,c,s)|json!({"case":name,"case_sha256":c,"script_sha256":s})).collect::<Vec<_>>(),"wall_seconds":5,"per_process_cpu_seconds":4,"address_space_bytes":805306368u64}),
    )?;
    let mut observed = vec![];
    for (name, c, s, _, _) in prepared {
        let result = Command::new("prlimit")
            .args([
                "--as=805306368",
                "--cpu=4:4",
                "--",
                "timeout",
                "--signal=KILL",
                "5",
            ])
            .arg(engine)
            .arg("-q")
            .arg(out.join(name).join("input.sing"))
            .output()?;
        fs::write(out.join(name).join("stdout"), &result.stdout)?;
        fs::write(out.join(name).join("stderr"), &result.stderr)?;
        if !result.status.success() {
            return Err(format!("native M1 control failed: {name}: {}", result.status).into());
        }
        let basis = recovery::parse_basis(
            std::str::from_utf8(&result.stdout)?,
            s.variables.len(),
            &c.field()?,
        )?;
        let mut limits = recovery::Limits::default();
        let (assignments, triples) = recovery::checked_triples(&c, &s, &basis, &mut limits)?;
        observed.push((name, c.id, basis.engine_reported_unit, assignments, triples));
    }
    // Oracle data is parsed only after native basis computation and recovery.
    let expected: Value = serde_json::from_slice(&known_bytes)?;
    let mut rows = vec![];
    let mut all_match = true;
    for (name, id, unit, assignments, triples) in observed {
        let mut want = vec![];
        if let Some(v) = expected.get(&id) {
            for v in v.as_array().ok_or("bad oracle shape")? {
                let mut us = triple(v)?.to_vec();
                us.sort();
                want.push(us);
            }
        }
        want.sort();
        want.dedup();
        let matched = triples == want;
        all_match &= matched;
        rows.push(json!({"case":name,"engine_reported_unit":unit,"basis_assignments":assignments,"u_triples":triples.iter().map(|v|v.iter().map(ToString::to_string).collect::<Vec<_>>()).collect::<Vec<_>>(),"matches_complete_M1_oracle":matched,"absence_certified":false}));
    }
    save(
        out.join("native-recovery-post-call.json"),
        &json!({"schema":"torus-s4.native-recovery-post-call/v1","pre_call_sha256":hash_file(out.join("native-recovery-pre-call.json"))?,"cases":rows,"all_controls_match":all_match,"pcc_standing":"unverified"}),
    )?;
    if !all_match {
        return Err("M1 recovered triples differ from complete oracle".into());
    }
    Ok(())
}
fn run() -> Result<()> {
    let a: Vec<_> = env::args().collect();
    match a.get(1).map(String::as_str){
        Some("freeze") if a.len()==3=>freeze(Path::new(&a[2])),
        Some("qualify") if a.len()==5=>qualify(Path::new(&a[2]),Path::new(&a[3]),Path::new(&a[4])),
        Some("check") if a.len()==4=>check(Path::new(&a[2]),Path::new(&a[3])),
        Some("prepare-engine") if a.len()==4=>prepare_engine(Path::new(&a[2]),Path::new(&a[3])),
        Some("recover") if a.len()==5=>recover(Path::new(&a[2]),Path::new(&a[3]),Path::new(&a[4])),
        Some("prepare-tree") if a.len()==4=>prepare_tree(Path::new(&a[2]),Path::new(&a[3])),
        Some("recover-tree") if a.len()==5=>recover_tree(Path::new(&a[2]),Path::new(&a[3]),Path::new(&a[4])),
        Some("native-tree-controls") if a.len()==4=>native_tree_controls(Path::new(&a[2]),Path::new(&a[3])),
        Some("native-controls") if a.len()==6=>native_controls(Path::new(&a[2]),Path::new(&a[3]),Path::new(&a[4]),Path::new(&a[5])),
        _=>Err("usage: qualifier freeze NEW_DIR | qualify CASES KNOWN.json NEW_OUTPUT_DIR | check CASE.json TRIPLE.json | prepare-engine CASE.json NEW_DIR | recover CASE.json TRANSCRIPT NEW_DIR".into())
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
