//! Bind complete originals and every literal counter/cycle source byte.
#[path = "../../../../crypto/src/hash/sha256.rs"]
#[allow(dead_code)]
// Preserve the frozen upstream block iterator and every original test.
#[allow(clippy::chunks_exact_to_as_chunks)]
mod original_sha256;
use std::{fs, path::PathBuf};

fn section<'a>(s: &'a str, start: &str, end: &str) -> &'a str {
    assert_eq!(s.matches(start).count(), 1);
    assert_eq!(s.matches(end).count(), 1);
    &s[s.find(start).unwrap()..s.find(end).unwrap()]
}
fn digest(s: &str) -> String {
    original_sha256::sha256(s.as_bytes())
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}
fn main() {
    let p = PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").unwrap());
    let ic = fs::read_to_string(p.join("original-source/ic.rs")).unwrap();
    let common = fs::read_to_string(p.join("original-source/common.rs")).unwrap();
    assert_eq!(
        digest(&ic),
        "ec20c87ed0be8c663af9965b4f0caf5bfe25b58d629a1896078026d52cfee90c"
    );
    assert_eq!(
        digest(&common),
        "832fd28810909194875a9438e164ec1b45dcefbaa83257b4e3fad3095ef865d6"
    );
    let literal = [
        "#![allow(dead_code)]\nuse super::original_counters::{bump_ladd, bump_lmul};\nuse std::collections::HashMap;\n",
        "pub type P3 = [u64; 3];\n",
        "pub type Row = Vec<(u32, u64)>;\n",
        section(&ic, "pub struct Rel2Out {", "pub fn find_relations_2lp("),
        section(&ic, "#[inline(always)]\npub fn lm(", "#[inline(always)]\npub fn ls("),
        section(&ic, "fn vec_from(map: HashMap<u32, u64>)", "/// After the factor-base logs and eta are known,"),
    ].concat();
    assert_eq!(
        fs::read_to_string(p.join("src/original_cycles.rs")).unwrap(),
        literal,
        "literal original cycle source changed"
    );
    assert_eq!(
        fs::read_to_string(p.join("src/original_counters.rs")).unwrap(),
        &common[..common.find("pub struct Rng(").unwrap()],
        "original counters changed"
    );
    for path in [
        "build.rs",
        "original-source/ic.rs",
        "original-source/common.rs",
        "src/original_cycles.rs",
        "src/original_counters.rs",
    ] {
        println!("cargo:rerun-if-changed={path}");
    }
}
