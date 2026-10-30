//! Opt-in single-thread instrumentation for native end-to-end harness adapters.
//! Group calls are counted; meter events remain unpriced diagnostics. Clocks
//! are separate from deterministic counters and never affect solver choices.

use crate::{invalid, overflow, Result};
use std::cell::RefCell;
use std::collections::BTreeMap;
use std::marker::PhantomData;
use std::rc::Rc;
use std::time::Instant;

/// One exclusive phase, including failed attempts.
#[derive(Clone, Debug, Default)]
pub struct Phase {
    /// Actual checked point-addition calls, including identity/inverse cases.
    pub adds: u64,
    /// Checked equal-nonidentity-input addition calls.
    pub doubles: u64,
    /// Scalar-multiplication calls (their group calls are counted separately).
    pub scalar_mults: u64,
    /// Charged meter-step attempts, not calibrated primitive operations.
    pub meter_steps: u64,
    /// Exclusive elapsed nanoseconds; never used as a deterministic counter.
    pub wall_ns: u64,
}
/// Completed observer snapshot.
#[derive(Clone, Debug)]
pub struct Snapshot {
    /// Exclusive cold phases, summed across retries.
    pub phases: BTreeMap<String, Phase>,
    /// Canonical exclusive online phases, from first query through final replay.
    pub online_phases_ns: BTreeMap<String, u64>,
    /// None when no target-dependent query was entered.
    pub online_wall_ns: Option<u64>,
}
struct Recorder {
    phase: &'static str,
    last: Instant,
    online: Option<Instant>,
    phases: BTreeMap<String, Phase>,
    online_phases: BTreeMap<String, u64>,
}
thread_local! { static ACTIVE: RefCell<Option<Recorder>> = const {RefCell::new(None)}; }
fn add(value: &mut u64, n: u64) -> Result<()> {
    *value = value
        .checked_add(n)
        .ok_or_else(|| overflow("native observer counter"))?;
    Ok(())
}
fn online_name(phase: &str) -> &'static str {
    match phase {
        "relation_search" | "network_build" | "contraction" => "target_PDP",
        "relation_check" | "witness_check" | "matrix_build" => "target_relation_check",
        "linear_algebra" | "recovery_check" => "target_recovery_check",
        _ => "target_query", // includes target-caused seed/base retries
    }
}
impl Recorder {
    fn flush(&mut self, now: Instant) -> Result<()> {
        let elapsed = u64::try_from(now.duration_since(self.last).as_nanos())
            .map_err(|_| overflow("native phase clock"))?;
        add(
            &mut self.phases.entry(self.phase.into()).or_default().wall_ns,
            elapsed,
        )?;
        if self.online.is_some() {
            add(
                self.online_phases
                    .entry(online_name(self.phase).into())
                    .or_default(),
                elapsed,
            )?;
        }
        self.last = now;
        Ok(())
    }
}
/// A scoped thread-local observer; cannot move to another thread or nest.
/// Dropping it clears instrumentation even when a solve exits by error/panic.
pub struct Session {
    active: bool,
    thread: PhantomData<Rc<()>>,
}
impl Session {
    /// Start cold setup accounting without changing any solver RNG or policy.
    pub fn start() -> Result<Self> {
        ACTIVE.with(|slot| {
            let mut slot = slot.borrow_mut();
            if slot.is_some() {
                return Err(invalid("nested native metric sessions"));
            }
            *slot = Some(Recorder {
                phase: "setup",
                last: Instant::now(),
                online: None,
                phases: BTreeMap::new(),
                online_phases: BTreeMap::new(),
            });
            Ok(Self {
                active: true,
                thread: PhantomData,
            })
        })
    }
    /// Finish and detach all observations. Wall fields are intrinsically
    /// nondeterministic; only the event counts are suitable for exact replay.
    pub fn finish(mut self) -> Result<Snapshot> {
        let result = ACTIVE.with(|slot| {
            let mut recorder = slot
                .borrow_mut()
                .take()
                .ok_or_else(|| invalid("missing native metrics session"))?;
            let now = Instant::now();
            recorder.flush(now)?;
            let online_wall_ns = recorder
                .online
                .map(|start| {
                    u64::try_from(now.duration_since(start).as_nanos())
                        .map_err(|_| overflow("native online clock"))
                })
                .transpose()?;
            if let Some(expected) = online_wall_ns {
                let sum = recorder.online_phases.values().try_fold(0u64, |n, &v| {
                    n.checked_add(v).ok_or_else(|| overflow("native phase sum"))
                })?;
                if sum != expected {
                    return Err(crate::integrity("native online phase partition"));
                }
            }
            Ok(Snapshot {
                phases: recorder.phases,
                online_phases_ns: recorder.online_phases,
                online_wall_ns,
            })
        });
        self.active = false;
        result
    }
}
impl Drop for Session {
    fn drop(&mut self) {
        if self.active {
            ACTIVE.with(|slot| {
                slot.borrow_mut().take();
            });
        }
    }
}
/// Switch the exclusive stage. This is a no-op unless an observer is active.
pub fn phase(name: &'static str) -> Result<()> {
    ACTIVE.with(|slot| {
        if let Some(recorder) = slot.borrow_mut().as_mut() {
            let now = Instant::now();
            recorder.flush(now)?;
            if name == "relation_target" && recorder.online.is_none() {
                recorder.online = Some(now);
            }
            recorder.phase = name;
        }
        Ok(())
    })
}
pub(crate) fn work(n: u64) -> Result<()> {
    ACTIVE.with(|slot| {
        if let Some(r) = slot.borrow_mut().as_mut() {
            add(
                &mut r.phases.entry(r.phase.into()).or_default().meter_steps,
                n,
            )?;
        }
        Ok(())
    })
}
pub(crate) fn group(double: bool) -> Result<()> {
    ACTIVE.with(|slot| {
        if let Some(r) = slot.borrow_mut().as_mut() {
            let p = r.phases.entry(r.phase.into()).or_default();
            add(if double { &mut p.doubles } else { &mut p.adds }, 1)?;
        }
        Ok(())
    })
}
pub(crate) fn scalar() -> Result<()> {
    ACTIVE.with(|slot| {
        if let Some(r) = slot.borrow_mut().as_mut() {
            add(
                &mut r.phases.entry(r.phase.into()).or_default().scalar_mults,
                1,
            )?;
        }
        Ok(())
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn scoped_observer_keeps_exact_counters_separate_from_clocks_and_cleans_up() {
        let session = Session::start().unwrap();
        assert!(Session::start().is_err());
        work(3).unwrap();
        group(false).unwrap();
        phase("relation_target").unwrap();
        scalar().unwrap();
        phase("relation_search").unwrap();
        work(7).unwrap();
        group(true).unwrap();
        phase("recovery_check").unwrap();
        let snapshot = session.finish().unwrap();
        assert_eq!(snapshot.phases["setup"].meter_steps, 3);
        assert_eq!(snapshot.phases["setup"].adds, 1);
        assert_eq!(snapshot.phases["relation_search"].doubles, 1);
        assert_eq!(snapshot.phases["relation_target"].scalar_mults, 1);
        assert_eq!(
            snapshot.online_phases_ns.values().sum::<u64>(),
            snapshot.online_wall_ns.unwrap()
        );
        {
            let _guard = Session::start().unwrap();
        }
        Session::start().unwrap().finish().unwrap();
    }
}
