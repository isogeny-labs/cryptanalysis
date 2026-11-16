//! Entire ordered records, reconstructed using the basis-span transport route.
//! Serialization and original finite-space helpers are shared and declared.
use chained_n4_original_kernel_census::{assert_order, records, PREFIX};
use serde_json::{json, Value};
use std::{fs, path::Path};
fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    assert!(args.len() == 4 || args.len() == 5);
    let mode = &args[1];
    assert!(mode == "--freeze" || mode == "--compare");
    let (native, output) = if mode == "--freeze" {
        assert_eq!(args.len(), 4);
        (&args[2], &args[3])
    } else {
        assert_eq!(args.len(), 5);
        (&args[3], &args[4])
    };
    assert!(!Path::new(output).exists());
    let text = fs::read_to_string(native).unwrap();
    assert_eq!(
        text.lines()
            .filter(|line| line.starts_with(
                "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"
            ))
            .count(),
        1
    );
    let actual = text
        .lines()
        .filter_map(|line| {
            line.find(PREFIX).map(|i| {
                let (kind, data) = line[i..].split_once(' ').unwrap();
                json!({"kind":kind,"data":serde_json::from_str::<Value>(data).unwrap()})
            })
        })
        .collect::<Vec<_>>();
    assert_order(&actual);
    let independently_transported = records(true);
    assert_eq!(
        actual, independently_transported,
        "entire bitset output must equal pinned-input basis-span reconstruction"
    );
    if mode == "--compare" {
        let expected: Vec<Value> = serde_json::from_slice(&fs::read(&args[2]).unwrap()).unwrap();
        assert_order(&expected);
        assert_eq!(
            expected, actual,
            "all311 whole records and every field required"
        );
    }
    fs::write(output, serde_json::to_vec(&actual).unwrap()).unwrap();
}
