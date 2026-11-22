//! Optional exclusive accounting of the target-dependent search interval.
use std::time::{Duration, Instant};

/// Producer-side wall-clock partition of one profiled search.
///
/// These disjoint intervals include clock-reading overhead; nothing is
/// subtracted. They exclude reusable preparation, CLI/report work and any
/// independent replay. They do not qualify a performance measurement.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct SearchPhases {
    /// Target/config validation, jump/lane initialization and scratch allocation.
    pub initialization: Duration,
    /// Public-coefficient updates and batched target-walk additions.
    pub target_walk: Duration,
    /// Membership circuit/direct subtraction and checked signed decomposition.
    pub decomposition: Duration,
    /// Replay of a new distinct row's public coefficient equation.
    pub row_validation: Duration,
    /// Relation storage, gain-graph insertion and dependency expansion.
    pub graph_recovery: Duration,
    /// Complete local certificate replay, including the recovered scalar.
    pub certificate_replay: Duration,
    /// Query/row counters, deduplication, limits and outcome construction.
    pub bookkeeping: Duration,
    /// Entire core search interval; exactly the sum of the seven phases.
    pub total: Duration,
    /// Boundary clock reads, including the initial and final boundary reads.
    pub clock_reads: u64,
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub(crate) enum Phase {
    Initialization,
    TargetWalk,
    Decomposition,
    RowValidation,
    GraphRecovery,
    CertificateReplay,
    Bookkeeping,
}

pub(crate) trait Profiler {
    fn enter(&mut self, phase: Phase);
}

// Monomorphizes away in the original, unprofiled APIs.
impl Profiler for () {
    #[inline(always)]
    fn enter(&mut self, _: Phase) {}
}

pub(crate) trait Clock {
    fn now(&mut self) -> Duration;
}

pub(crate) struct Monotonic(Instant);
impl Clock for Monotonic {
    fn now(&mut self) -> Duration {
        self.0.elapsed()
    }
}

pub(crate) struct Recorder<C = Monotonic> {
    clock: C,
    start: Duration,
    last: Duration,
    phase: Phase,
    phases: SearchPhases,
}

impl Recorder {
    pub(crate) fn start() -> Self {
        Self::new(Monotonic(Instant::now()))
    }
}

impl<C: Clock> Recorder<C> {
    fn new(mut clock: C) -> Self {
        let start = clock.now();
        Self {
            clock,
            start,
            last: start,
            phase: Phase::Initialization,
            phases: SearchPhases {
                clock_reads: 1,
                ..SearchPhases::default()
            },
        }
    }
    fn charge(&mut self) {
        let now = self.clock.now();
        let elapsed = now - self.last;
        self.last = now;
        self.phases.clock_reads += 1;
        let phase = match self.phase {
            Phase::Initialization => &mut self.phases.initialization,
            Phase::TargetWalk => &mut self.phases.target_walk,
            Phase::Decomposition => &mut self.phases.decomposition,
            Phase::RowValidation => &mut self.phases.row_validation,
            Phase::GraphRecovery => &mut self.phases.graph_recovery,
            Phase::CertificateReplay => &mut self.phases.certificate_replay,
            Phase::Bookkeeping => &mut self.phases.bookkeeping,
        };
        *phase += elapsed;
    }
    pub(crate) fn finish(mut self) -> SearchPhases {
        self.charge();
        self.phases.total = self.last - self.start;
        self.phases
    }
}

impl<C: Clock> Profiler for Recorder<C> {
    fn enter(&mut self, phase: Phase) {
        if phase != self.phase {
            self.charge();
            self.phase = phase;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct ScriptedClock(std::vec::IntoIter<u64>);
    impl Clock for ScriptedClock {
        fn now(&mut self) -> Duration {
            Duration::from_nanos(self.0.next().expect("unexpected boundary read"))
        }
    }
    #[test]
    fn disjoint_intervals_include_repeated_phases_and_the_final_tail() {
        let mut recorder = Recorder::new(ScriptedClock(
            vec![100, 110, 130, 160, 165, 170, 177, 188, 200, 225].into_iter(),
        ));
        for phase in [
            Phase::TargetWalk,
            Phase::Decomposition,
            Phase::Bookkeeping,
            Phase::TargetWalk,
            Phase::RowValidation,
            Phase::GraphRecovery,
            Phase::CertificateReplay,
            Phase::Bookkeeping,
        ] {
            recorder.enter(phase);
            recorder.enter(phase); // No extra read or double charging.
        }
        let result = recorder.finish();
        let ns = |d: Duration| d.as_nanos();
        assert_eq!(ns(result.initialization), 10);
        assert_eq!(ns(result.target_walk), 25);
        assert_eq!(ns(result.decomposition), 30);
        assert_eq!(ns(result.row_validation), 7);
        assert_eq!(ns(result.graph_recovery), 11);
        assert_eq!(ns(result.certificate_replay), 12);
        assert_eq!(ns(result.bookkeeping), 30);
        assert_eq!(ns(result.total), 125);
        assert_eq!(result.clock_reads, 10);
    }
    #[test]
    fn early_exit_accounts_for_initialization_without_inventing_search_work() {
        let recorder = Recorder::new(ScriptedClock(vec![50, 61].into_iter()));
        let result = recorder.finish();
        assert_eq!(result.initialization, result.total);
        assert_eq!(result.total, Duration::from_nanos(11));
        assert_eq!(result.clock_reads, 2);
        assert_eq!(result.target_walk, Duration::ZERO);
        assert_eq!(result.certificate_replay, Duration::ZERO);
    }
}
