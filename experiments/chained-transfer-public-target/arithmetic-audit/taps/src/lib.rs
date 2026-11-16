//! Deterministic serial source-operation census. No prices or legacy counters.
use std::cell::RefCell;
use std::collections::BTreeMap;
use std::sync::OnceLock;
use std::thread::ThreadId;

type Key = (usize, &'static str, u64, &'static str);
static OWNER: OnceLock<ThreadId> = OnceLock::new();
#[derive(Default)]
struct Ledger {
    scope: usize,
    labels: Vec<String>,
    counts: BTreeMap<Key, u64>,
}
thread_local! { static LEDGER: RefCell<Ledger> = RefCell::new(Ledger {
    scope: 0, labels: vec!["residual".into()], counts: BTreeMap::new(),
}); }
fn owner() {
    let id = std::thread::current().id();
    assert_eq!(
        *OWNER.get_or_init(|| id),
        id,
        "unexpected arithmetic thread"
    );
}
/// Count only at the actual expression or nondelegating field leaf.
#[inline]
pub fn hit(backend: &'static str, modulus: u64, operation: &'static str, n: u64) {
    owner();
    if n == 0 {
        return;
    }
    LEDGER.with(|cell| {
        let mut l = cell.borrow_mut();
        let scope = l.scope;
        let count = l
            .counts
            .entry((scope, backend, modulus, operation))
            .or_default();
        *count = count.checked_add(n).expect("arithmetic census overflow");
    });
}
pub struct Scope(usize);
impl Drop for Scope {
    fn drop(&mut self) {
        owner();
        LEDGER.with(|l| l.borrow_mut().scope = self.0);
    }
}
pub fn scope(label: impl Into<String>) -> Scope {
    owner();
    let label = label.into();
    LEDGER.with(|cell| {
        let mut l = cell.borrow_mut();
        let old = l.scope;
        let next = l
            .labels
            .iter()
            .position(|s| s == &label)
            .unwrap_or_else(|| {
                l.labels.push(label);
                l.labels.len() - 1
            });
        l.scope = next;
        Scope(old)
    })
}
pub fn within<T>(label: impl Into<String>, f: impl FnOnce() -> T) -> T {
    let _scope = scope(label);
    f()
}
pub fn count(label: &str, backend: &str, modulus: u64, op: &str) -> u64 {
    owner();
    LEDGER.with(|cell| {
        let l = cell.borrow();
        l.counts
            .iter()
            .filter(|((s, b, p, o), _)| {
                l.labels[*s] == label && *b == backend && *p == modulus && *o == op
            })
            .map(|(_, n)| *n)
            .sum()
    })
}
pub fn total() -> u128 {
    owner();
    LEDGER.with(|l| l.borrow().counts.values().map(|&n| n as u128).sum())
}
pub fn snapshot() -> serde_json::Value {
    owner();
    LEDGER.with(|cell| {
        let l = cell.borrow();
        serde_json::json!({"schema":"n4-source-arithmetic-v1",
            "unit":"executed source-level field operations; unpriced; not machine instructions",
            "single_thread":true,"reset":"never reset by legacy Picard counters",
            "rows":l.counts.iter().map(|((s,b,p,o),n)| serde_json::json!({
                "scope":l.labels[*s],"backend":b,"modulus":p,"operation":o,"count":n
            })).collect::<Vec<_>>()})
    })
}
pub fn assert_no_unsupported() {
    owner();
    LEDGER.with(|cell| {
        let l = cell.borrow();
        assert!(
            !l.counts
                .iter()
                .any(|((_, _, _, op), n)| *op == "unsupported_entry" && *n > 0),
            "executed backend has incomplete arithmetic coverage"
        );
    });
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn nested_scopes_checked_counts_and_foreign_thread_rejection() {
        let first = total();
        within("outer", || {
            hit("unit", 223, "mul", 2);
            within("inner", || hit("unit", 223, "mul", 3));
            hit("unit", 223, "mul", 5);
        });
        assert_eq!(count("outer", "unit", 223, "mul"), 7);
        assert_eq!(count("inner", "unit", 223, "mul"), 3);
        assert_eq!(total(), first + 10);
        assert!(std::thread::spawn(|| hit("unit", 223, "mul", 1))
            .join()
            .is_err());
        assert_eq!(total(), first + 10);
        assert_no_unsupported();
    }
}
