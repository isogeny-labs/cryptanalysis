//! Deterministic serial source-operation census. No prices or legacy counters.
use std::cell::RefCell;
use std::collections::BTreeMap;
use std::sync::OnceLock;
use std::thread::ThreadId;

type Key = (usize, usize, &'static str, u64, &'static str);
static OWNER: OnceLock<ThreadId> = OnceLock::new();
// Only observer storage changes. Canonical keys, units and checked increments
// are the original v2 contract; cache placement never defines key equality.
struct Counters {
    index: BTreeMap<Key, usize>,
    values: Vec<u64>,
    hot: [Option<(Key, usize)>; 128],
}
impl Default for Counters {
    fn default() -> Self {
        Self {
            index: BTreeMap::new(),
            values: Vec::new(),
            hot: [None; 128],
        }
    }
}
impl Counters {
    #[inline]
    fn slot(key: Key) -> usize {
        (key.0.wrapping_mul(17)
            ^ key.1.wrapping_mul(131)
            ^ key.3 as usize
            ^ (key.2.as_ptr() as usize).rotate_right(4)
            ^ (key.4.as_ptr() as usize).rotate_right(7))
            & 127
    }
    #[inline]
    fn increment(&mut self, key: Key, n: u64) {
        let slot = Self::slot(key);
        let cached = self.hot[slot].and_then(|(old, i)| (old == key).then_some(i));
        let i = cached.unwrap_or_else(|| {
            let i = if let Some(&i) = self.index.get(&key) {
                i
            } else {
                let i = self.values.len();
                self.values.push(0);
                assert!(self.index.insert(key, i).is_none());
                i
            };
            self.hot[slot] = Some((key, i));
            i
        });
        self.values[i] = self.values[i]
            .checked_add(n)
            .expect("arithmetic census overflow");
    }
    fn iter(&self) -> impl Iterator<Item = (&Key, &u64)> + '_ {
        self.index
            .iter()
            .map(move |(key, &i)| (key, &self.values[i]))
    }
    fn values(&self) -> std::slice::Iter<'_, u64> {
        self.values.iter()
    }
}
#[derive(Default)]
struct Ledger {
    phase: usize,
    phases: Vec<String>,
    scope: usize,
    labels: Vec<String>,
    counts: Counters,
}
thread_local! { static LEDGER: RefCell<Ledger> = RefCell::new({
    // This runs on EVERY enabled thread's first observer API entry, before a
    // count, zero hit, phase, scope or snapshot can be accepted. No recursion
    // through owner(): initialization itself performs the global check.
    if observer_enabled() {
        let id = std::thread::current().id();
        assert_eq!(*OWNER.get_or_init(|| id), id, "unexpected arithmetic thread");
    }
    Ledger {
        phase: 0, phases: vec!["residual".into()], scope: 0,
        labels: vec!["residual".into()], counts: Counters::default(),
    }
}); }
// Versioned census mode: immutable for each process. Disabled mode is for
// complete unfiltered mathematical parity only, never an accepted census.
static OBSERVER: OnceLock<bool> = OnceLock::new();
pub fn observer_enabled() -> bool {
    *OBSERVER.get_or_init(
        || match std::env::var("N4_ARITHMETIC_OBSERVER").as_deref() {
            Err(std::env::VarError::NotPresent) | Ok("enabled") => true,
            Ok("disabled") => false,
            _ => panic!("unknown arithmetic observer mode"),
        },
    )
}
fn owner() {
    if observer_enabled() {
        // The thread-local initializer checks the global owner once. Repeated
        // accesses need no ThreadId acquisition or global-owner comparison.
        LEDGER.with(|_| ());
    }
}
/// Count only at the actual expression or nondelegating field leaf.
#[inline]
pub fn hit(backend: &'static str, modulus: u64, operation: &'static str, n: u64) {
    if !observer_enabled() {
        return;
    }
    LEDGER.with(|cell| {
        // Enter the TLS owner guard even for a zero hit, preserving strict
        // first-entry rejection rather than accepting a foreign no-op.
        if n == 0 {
            return;
        }
        let mut l = cell.borrow_mut();
        let scope = l.scope;
        let phase = l.phase;
        l.counts
            .increment((phase, scope, backend, modulus, operation), n);
    });
}
/// Orthogonal execution phase; old leaf/function scope names remain unchanged.
pub struct Phase(usize);
impl Drop for Phase {
    fn drop(&mut self) {
        owner();
        LEDGER.with(|cell| cell.borrow_mut().phase = self.0);
    }
}
pub fn phase(label: &str) -> Phase {
    owner();
    LEDGER.with(|cell| {
        let mut l = cell.borrow_mut();
        let previous = l.phase;
        let name = if previous == 0 {
            label.to_owned()
        } else {
            format!("{}/{}", l.phases[previous], label)
        };
        let next = l.phases.iter().position(|p| p == &name).unwrap_or_else(|| {
            l.phases.push(name);
            l.phases.len() - 1
        });
        l.phase = next;
        Phase(previous)
    })
}
pub fn with_phase<T>(label: &str, f: impl FnOnce() -> T) -> T {
    let _phase = phase(label);
    f()
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
            .filter(|((_, s, b, p, o), _)| {
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
        serde_json::json!({"schema":"n4-source-arithmetic-v2",
            "unit":"executed source-level field operations; unpriced; not machine instructions",
            "single_thread":true,"reset":"never reset by legacy Picard counters",
            "rows":l.counts.iter().map(|((phase,s,b,p,o),n)| serde_json::json!({
                "phase":l.phases[*phase],"scope":l.labels[*s],"backend":b,"modulus":p,"operation":o,"count":n
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
                .any(|((_, _, _, _, op), n)| *op == "unsupported_entry" && *n > 0),
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
        with_phase("phase-a", || {
            within("phase-test", || hit("unit", 223, "mul", 2))
        });
        with_phase("phase-b", || {
            within("phase-test", || hit("unit", 223, "mul", 3))
        });
        assert_eq!(count("phase-test", "unit", 223, "mul"), 5);
        let phase_snapshot = snapshot();
        assert_eq!(
            phase_snapshot["rows"]
                .as_array()
                .unwrap()
                .iter()
                .filter(|r| r["scope"] == "phase-test")
                .count(),
            2
        );
        assert_eq!(total(), first + 15);

        // Actual direct-cache collision, fallback and repeated-hit paths must
        // preserve independent exact per-key counts and canonical snapshots.
        let backend = "unit";
        let operation = "mul";
        assert_eq!(
            Counters::slot((0, 0, backend, 223, operation)),
            Counters::slot((0, 0, backend, 351, operation))
        );
        within("cache-collision", || {
            hit(backend, 223, operation, 2);
            hit(backend, 351, operation, 3);
            hit(backend, 223, operation, 5);
            hit(backend, 223, operation, 7);
        });
        assert_eq!(count("cache-collision", backend, 223, operation), 14);
        assert_eq!(count("cache-collision", backend, 351, operation), 3);
        assert_eq!(total(), first + 32);
        let before = snapshot();
        hit("unit", 223, "zero", 0);
        assert_eq!(snapshot(), before);
        for entry in 0..4 {
            assert!(std::thread::spawn(move || match entry {
                0 => hit("unit", 223, "mul", 0),
                1 => {
                    let _ = phase("foreign-first");
                }
                2 => {
                    let _ = scope("foreign-first");
                }
                _ => {
                    let _ = snapshot();
                }
            })
            .join()
            .is_err());
            assert_eq!(snapshot(), before);
        }
        within("checked-overflow", || {
            hit("unit", 223, "overflow", u64::MAX);
            assert!(std::panic::catch_unwind(|| hit("unit", 223, "overflow", 1)).is_err());
            assert_eq!(count("checked-overflow", "unit", 223, "overflow"), u64::MAX);
        });
        assert_eq!(total(), first + 32 + u64::MAX as u128);
        assert_no_unsupported();
    }
}
