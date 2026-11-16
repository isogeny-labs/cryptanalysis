//! Retain the entire witness population while changing one scalar certificate.
use serde_json::Value;
use std::{
    env, fs,
    io::{BufRead, BufReader, BufWriter, Write},
};
fn main() {
    let a: Vec<_> = env::args().collect();
    assert_eq!(a.len(), 3);
    assert!(!std::path::Path::new(&a[2]).exists());
    let mut out = BufWriter::new(
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&a[2])
            .unwrap(),
    );
    let mut changed = false;
    let mut calls = 0;
    for line in BufReader::new(fs::File::open(&a[1]).unwrap()).lines() {
        let mut v: Value = serde_json::from_str(&line.unwrap()).unwrap();
        if v["kind"] == "call" {
            calls += 1;
            if !changed {
                let w = &mut v["entire_point_witnesses"][0]["witness"];
                assert_eq!(w["status"], "witness");
                let old = w["scalar"].as_u64().unwrap();
                w["scalar"] = Value::from((old + 1) % 2_773_073);
                changed = true;
            }
        }
        writeln!(out, "{v}").unwrap();
    }
    assert!(changed);
    assert_eq!(calls, 60);
    out.flush().unwrap();
}
