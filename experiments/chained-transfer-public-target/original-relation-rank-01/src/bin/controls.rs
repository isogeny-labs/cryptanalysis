//! Whole-certificate mathematical mutations. No record is filtered or removed.
use serde_json::Value;
use std::{
    env, fs,
    io::{BufRead, BufReader, BufWriter, Write},
};
const P: u64 = 2_773_073;
fn main() {
    let a: Vec<_> = env::args().collect();
    assert_eq!(a.len(), 4, "CERT MATRIX_OUT KERNEL_OUT");
    for p in &a[2..] {
        assert!(!std::path::Path::new(p).exists());
    }
    let mut matrix = BufWriter::new(
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&a[2])
            .unwrap(),
    );
    let mut kernel = BufWriter::new(
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&a[3])
            .unwrap(),
    );
    let mut changed = false;
    let mut lines = 0;
    for line in BufReader::new(fs::File::open(&a[1]).unwrap()).lines() {
        let line = line.unwrap();
        let original: Value = serde_json::from_str(&line).unwrap();
        let mut m = original.clone();
        let mut k = original.clone();
        if !changed && original["kind"] == "call" {
            let val = m["certificates"][0]["rref"][0][0].as_u64().unwrap();
            m["certificates"][0]["rref"][0][0] = Value::from((val + 1) % P);
            let c = original["certificates"][0]["dense_mod_ell_summed_original"][0]
                .as_array()
                .unwrap()
                .iter()
                .position(|v| v.as_u64().unwrap() != 0)
                .expect("constrained column");
            let val = k["candidate_full_known_or_unknown"][c].as_u64().unwrap();
            k["candidate_full_known_or_unknown"][c] = Value::from((val + 1) % P);
            changed = true;
        }
        writeln!(matrix, "{m}").unwrap();
        writeln!(kernel, "{k}").unwrap();
        lines += 1;
    }
    assert!(changed);
    assert_eq!(lines, 62);
    matrix.flush().unwrap();
    kernel.flush().unwrap();
}
