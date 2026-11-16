//! Bounded graph-aware selection among already replayed two-slot witnesses.
//!
//! The policy sees an opaque witness and a connectivity predicate, never a
//! target's scalar coefficients. The prepared-table caller supplies one scan
//! step per candidate subtraction and exact lookup, including misses. It must
//! perform the original arithmetic replay before returning `Witness` and keep
//! slot identities in that payload. Connectivity only selects a witness; a
//! cycle may still have an unusable combined coefficient in the collector.
//!
//! A zero extra-scan cap returns the original first witness without consulting
//! the graph. With a positive cap, the first cycle-closing witness wins, with
//! at most that many further candidate scans after the first witness. Misses
//! consume that budget. If none closes a cycle, the first witness is retained.
//! Batch arithmetic, including any unused precomputed tail, remains the
//! caller's responsibility and is not made free by this selection budget.

use crate::{overflow, Meter, Result};

/// Event counts for the bounded selector, not calibrated work or runtime.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Statistics {
    /// Selector invocations, including later errors or exhausted queries.
    pub queries: u64,
    /// Candidate callback invocations, including exhaustion and callback errors.
    pub scan_calls: u64,
    /// Completed candidate checks (`Miss` or `Witness`), including the first hit.
    pub candidates: u64,
    /// Callback invocations after the first witness, including exhaustion/errors.
    pub extra_scan_calls: u64,
    /// Completed candidate checks after the first witness; misses count too.
    pub extra_candidates: u64,
    /// Already replayed witnesses returned by successful candidate checks.
    pub witnesses: u64,
    /// Connectivity callback invocations, including callback errors.
    pub graph_probes: u64,
    /// Cap-zero selections that did not inspect graph connectivity.
    pub first_hit_selections: u64,
    /// Selections whose connectivity callback reported a closing cycle.
    pub cycle_closing_selections: u64,
    /// Selections falling back to the original first witness after graph probing.
    pub fallback_selections: u64,
}

/// One prepared-table candidate check or the end of its selector-ordered scan.
pub(crate) enum ScanStep<W> {
    /// No further candidate exists. This is not a candidate check.
    Exhausted,
    /// One subtraction/lookup did not produce a full replayed witness.
    Miss,
    /// One subtraction/lookup produced this full replayed witness.
    Witness(W),
}

/// An unmodified witness selected from the caller's original scan order.
#[derive(Debug, PartialEq, Eq)]
pub(crate) struct Selection<W> {
    /// The original opaque payload, with slot order and point identity intact.
    pub witness: W,
    /// `None` for cap zero; otherwise the selected graph-connectivity result.
    pub closes_cycle: Option<bool>,
}

fn increment(value: &mut u64) -> Result<()> {
    *value = value
        .checked_add(1)
        .ok_or_else(|| overflow("witness policy statistics"))?;
    Ok(())
}

fn scan<W>(
    next: &mut impl FnMut(&mut Meter) -> Result<ScanStep<W>>,
    extra: bool,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<ScanStep<W>> {
    meter.charge(1, "witness policy scan")?;
    increment(&mut statistics.scan_calls)?;
    if extra {
        increment(&mut statistics.extra_scan_calls)?;
    }
    let step = next(meter)?;
    if !matches!(step, ScanStep::Exhausted) {
        increment(&mut statistics.candidates)?;
        if extra {
            increment(&mut statistics.extra_candidates)?;
        }
        if matches!(step, ScanStep::Witness(_)) {
            increment(&mut statistics.witnesses)?;
        }
    }
    Ok(step)
}

fn closes<W>(
    witness: &W,
    closes_cycle: &mut impl FnMut(&W, &mut Meter) -> Result<bool>,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<bool> {
    meter.charge(1, "witness policy graph probe")?;
    increment(&mut statistics.graph_probes)?;
    closes_cycle(witness, meter)
}

/// Select from a real selector-ordered scan with a bounded extra candidate cap.
///
/// `next` must complete at most one candidate subtraction/lookup per call, and
/// return `Witness` only after full arithmetic validation. The callbacks keep
/// charging their arithmetic, lookup, replay and graph work to `meter`; this
/// function additionally charges scan/probe bookkeeping. Its `W` payload must
/// not expose target coefficients or a planted scalar to the point/graph oracle.
///
/// Before the first witness, the original scan proceeds until a hit, exhaustion
/// or error. A cap of zero returns that first hit with no connectivity query.
/// A positive cap probes the first hit, then at most `extra_scan_cap` further
/// candidate checks, counting misses. The earliest cycle-closing hit wins;
/// otherwise the first witness remains selected. No resource or integrity
/// error becomes a miss or a successful fallback, even after the first hit.
pub(crate) fn choose<W>(
    extra_scan_cap: usize,
    mut next: impl FnMut(&mut Meter) -> Result<ScanStep<W>>,
    mut closes_cycle: impl FnMut(&W, &mut Meter) -> Result<bool>,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<Option<Selection<W>>> {
    increment(&mut statistics.queries)?;
    let first = loop {
        match scan(&mut next, false, statistics, meter)? {
            ScanStep::Exhausted => return Ok(None),
            ScanStep::Miss => {}
            ScanStep::Witness(witness) => break witness,
        }
    };
    if extra_scan_cap == 0 {
        increment(&mut statistics.first_hit_selections)?;
        return Ok(Some(Selection {
            witness: first,
            closes_cycle: None,
        }));
    }
    if closes(&first, &mut closes_cycle, statistics, meter)? {
        increment(&mut statistics.cycle_closing_selections)?;
        return Ok(Some(Selection {
            witness: first,
            closes_cycle: Some(true),
        }));
    }
    for _ in 0..extra_scan_cap {
        match scan(&mut next, true, statistics, meter)? {
            ScanStep::Exhausted => break,
            ScanStep::Miss => {}
            ScanStep::Witness(witness) => {
                if closes(&witness, &mut closes_cycle, statistics, meter)? {
                    increment(&mut statistics.cycle_closing_selections)?;
                    return Ok(Some(Selection {
                        witness,
                        closes_cycle: Some(true),
                    }));
                }
            }
        }
    }
    increment(&mut statistics.fallback_selections)?;
    Ok(Some(Selection {
        witness: first,
        closes_cycle: Some(false),
    }))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Error, Limits};

    fn meter() -> Meter {
        Meter::new(Limits::default())
    }

    #[test]
    fn cap_zero_keeps_first_hit_and_never_queries_graph() {
        let mut input = [None, None, Some(7), Some(11)].into_iter();
        let mut statistics = Statistics::default();
        let selected = choose(
            0,
            |_| {
                Ok(match input.next() {
                    Some(Some(w)) => ScanStep::Witness(w),
                    Some(None) => ScanStep::Miss,
                    None => ScanStep::Exhausted,
                })
            },
            |_, _| panic!("cap zero must not expose a graph probe"),
            &mut statistics,
            &mut meter(),
        )
        .unwrap()
        .unwrap();
        assert_eq!(selected.witness, 7);
        assert_eq!(selected.closes_cycle, None);
        assert_eq!(input.next(), Some(Some(11)));
        assert_eq!(statistics.scan_calls, 3);
        assert_eq!(statistics.candidates, 3);
        assert_eq!(statistics.extra_scan_calls, 0);
        assert_eq!(statistics.extra_candidates, 0);
        assert_eq!(statistics.graph_probes, 0);
        assert_eq!(statistics.first_hit_selections, 1);
    }

    #[test]
    fn exhausted_original_scan_remains_none_without_graph_work() {
        let mut remaining = 3;
        let mut statistics = Statistics::default();
        let answer: Option<Selection<u8>> = choose(
            16,
            |_| {
                if remaining == 0 {
                    Ok(ScanStep::Exhausted)
                } else {
                    remaining -= 1;
                    Ok(ScanStep::Miss)
                }
            },
            |_, _| panic!("there is no witness to probe"),
            &mut statistics,
            &mut meter(),
        )
        .unwrap();
        assert_eq!(answer, None);
        assert_eq!(statistics.scan_calls, 4);
        assert_eq!(statistics.candidates, 3);
        assert_eq!(statistics.witnesses, 0);
        assert_eq!(statistics.graph_probes, 0);
    }

    #[test]
    fn caps_four_and_sixteen_count_misses_not_only_witnesses() {
        for cap in [4usize, 16] {
            let mut position = 0;
            let mut statistics = Statistics::default();
            let selected = choose(
                cap,
                |_| {
                    let current = position;
                    position += 1;
                    Ok(if current == 0 || current == cap + 1 {
                        ScanStep::Witness(current)
                    } else {
                        ScanStep::Miss
                    })
                },
                |point, _| Ok(*point != 0),
                &mut statistics,
                &mut meter(),
            )
            .unwrap()
            .unwrap();
            assert_eq!(selected.witness, 0);
            assert_eq!(selected.closes_cycle, Some(false));
            assert_eq!(
                position,
                cap + 1,
                "the closing hit beyond the cap is untouched"
            );
            assert_eq!(statistics.extra_candidates, cap as u64);
            assert_eq!(statistics.extra_scan_calls, cap as u64);
            assert_eq!(statistics.graph_probes, 1);
            assert_eq!(statistics.fallback_selections, 1);
        }
    }

    #[test]
    fn earliest_cycle_closing_candidate_wins_at_the_budget_boundary() {
        let mut input = [Some(1), None, Some(2), Some(3)].into_iter();
        let mut statistics = Statistics::default();
        let selected = choose(
            2,
            |_| {
                Ok(match input.next() {
                    Some(Some(w)) => ScanStep::Witness(w),
                    Some(None) => ScanStep::Miss,
                    None => ScanStep::Exhausted,
                })
            },
            |w, _| Ok(*w >= 2),
            &mut statistics,
            &mut meter(),
        )
        .unwrap()
        .unwrap();
        assert_eq!(selected.witness, 2);
        assert_eq!(selected.closes_cycle, Some(true));
        assert_eq!(input.next(), Some(Some(3)));
        assert_eq!(statistics.extra_candidates, 2);
        assert_eq!(statistics.graph_probes, 2);
        assert_eq!(statistics.cycle_closing_selections, 1);
    }

    #[test]
    fn first_closing_witness_does_not_start_an_extra_scan() {
        let mut calls = 0;
        let mut statistics = Statistics::default();
        let answer = choose(
            16,
            |_| {
                calls += 1;
                assert_eq!(calls, 1);
                Ok(ScanStep::Witness(9))
            },
            |_, _| Ok(true),
            &mut statistics,
            &mut meter(),
        )
        .unwrap()
        .unwrap();
        assert_eq!(answer.witness, 9);
        assert_eq!(statistics.extra_scan_calls, 0);
        assert_eq!(statistics.graph_probes, 1);
    }

    #[test]
    fn exhaustion_after_first_witness_retains_that_exact_payload() {
        let mut input = [Some(vec![4, 5]), None].into_iter();
        let mut statistics = Statistics::default();
        let selected = choose(
            4,
            |_| {
                Ok(match input.next().flatten() {
                    Some(w) => ScanStep::Witness(w),
                    None => ScanStep::Exhausted,
                })
            },
            |_, _| Ok(false),
            &mut statistics,
            &mut meter(),
        )
        .unwrap()
        .unwrap();
        assert_eq!(selected.witness, vec![4, 5]);
        assert_eq!(statistics.extra_scan_calls, 1);
        assert_eq!(statistics.extra_candidates, 0);
        assert_eq!(statistics.fallback_selections, 1);
    }

    #[test]
    fn a_scan_error_after_first_hit_is_never_a_successful_fallback() {
        let failure = Error::Limit("candidate budget".into());
        let mut first = true;
        let mut statistics = Statistics::default();
        let result = choose(
            4,
            |_| {
                if first {
                    first = false;
                    Ok(ScanStep::Witness(1))
                } else {
                    Err(failure.clone())
                }
            },
            |_, _| Ok(false),
            &mut statistics,
            &mut meter(),
        );
        assert_eq!(result, Err(failure));
        assert_eq!(statistics.scan_calls, 2);
        assert_eq!(statistics.extra_scan_calls, 1);
        assert_eq!(statistics.candidates, 1);
        assert_eq!(statistics.fallback_selections, 0);
    }

    #[test]
    fn graph_errors_are_not_misses_or_fallbacks() {
        let failure = Error::Integrity("graph context".into());
        let mut statistics = Statistics::default();
        let result = choose(
            4,
            |_| Ok(ScanStep::Witness(1)),
            |_, _| Err(failure.clone()),
            &mut statistics,
            &mut meter(),
        );
        assert_eq!(result, Err(failure));
        assert_eq!(statistics.graph_probes, 1);
        assert_eq!(statistics.fallback_selections, 0);
    }

    #[test]
    fn policy_budget_errors_precede_unadmitted_callbacks() {
        let mut work = Meter::new(Limits {
            steps: 1,
            ..Limits::default()
        });
        let mut statistics = Statistics::default();
        let result = choose(
            4,
            |_| Ok(ScanStep::Witness(1)),
            |_, _| panic!("graph callback exceeds the policy bookkeeping budget"),
            &mut statistics,
            &mut work,
        );
        assert!(matches!(result, Err(Error::Limit(_))));
        assert_eq!(statistics.candidates, 1);
        assert_eq!(statistics.graph_probes, 0);
        assert_eq!(statistics.fallback_selections, 0);
    }

    #[test]
    fn callback_arithmetic_work_is_retained_in_the_shared_meter() {
        let mut work = meter();
        let mut statistics = Statistics::default();
        choose(
            1,
            |meter| {
                meter.charge(7, "test candidate arithmetic")?;
                Ok(ScanStep::Witness(1))
            },
            |_, meter| {
                meter.charge(5, "test graph arithmetic")?;
                Ok(true)
            },
            &mut statistics,
            &mut work,
        )
        .unwrap();
        assert_eq!(work.used, 14, "scan + candidate + probe + connectivity");
    }

    #[test]
    fn statistical_overflow_does_not_wrap_into_an_answer() {
        let mut statistics = Statistics {
            queries: u64::MAX,
            ..Statistics::default()
        };
        let result: Result<Option<Selection<u8>>> = choose(
            4,
            |_| panic!("overflow must precede scanning"),
            |_, _| panic!("overflow must precede probing"),
            &mut statistics,
            &mut meter(),
        );
        assert!(matches!(result, Err(Error::Limit(_))));
        assert_eq!(statistics.queries, u64::MAX);
    }

    #[test]
    fn slot_tags_and_original_witness_order_reach_connectivity_unchanged() {
        #[derive(Clone, Debug, PartialEq, Eq)]
        struct TaggedPoint {
            slot: u8,
            point: u8,
        }
        let first = [
            TaggedPoint { slot: 0, point: 7 },
            TaggedPoint { slot: 1, point: 7 },
        ];
        let second = [
            TaggedPoint { slot: 0, point: 8 },
            TaggedPoint { slot: 1, point: 7 },
        ];
        let mut input = [first.clone(), second.clone()].into_iter();
        let mut seen = Vec::new();
        let selected = choose(
            1,
            |_| Ok(input.next().map_or(ScanStep::Exhausted, ScanStep::Witness)),
            |w, _| {
                seen.push(w.clone());
                assert_eq!((w[0].slot, w[1].slot), (0, 1));
                Ok(w[0].point == 8)
            },
            &mut Statistics::default(),
            &mut meter(),
        )
        .unwrap()
        .unwrap();
        assert_eq!(seen, vec![first, second.clone()]);
        assert_eq!(selected.witness, second);
    }
}
