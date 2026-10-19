//! Conservative Bernoulli Chernoff bounds, with finite-query PRP coupling slack.
//! No normal approximation or chi-square tail is used for sparse events.
pub fn null_probability(rank: u32, zero_target: bool) -> f64 {
    let excluded_zero = 2.0_f64.powi(-128);
    (2.0_f64.powi(-(rank as i32)) - if zero_target { excluded_zero } else { 0.0 })
        / (1.0 - excluded_zero)
}

pub fn kl(x: f64, p: f64) -> f64 {
    if x == p {
        return 0.0;
    }
    if p == 0.0 || p == 1.0 {
        return f64::INFINITY;
    }
    let a = if x == 0.0 { 0.0 } else { x * (x / p).ln() };
    let b = if x == 1.0 {
        0.0
    } else {
        (1.0 - x) * ((1.0 - x) / (1.0 - p)).ln()
    };
    (a + b).max(0.0)
}

/// Chernoff upper bound for both tails at least as far from `p` as the
/// observed rate. The Bernoulli KL divergence is asymmetric, so doubling only
/// the observed tail's bound is not conservative when the observed rate is
/// below `p` (or above `p` for a skewed upper tail).
pub fn tail_bound(hits: u64, samples: u64, p: f64) -> f64 {
    if samples == 0 {
        return 1.0;
    }
    let observed = hits as f64 / samples as f64;
    let distance = (observed - p).abs();
    if distance == 0.0 {
        return 1.0;
    }

    // Bound the inclusive event |X/n - p| >= distance. Using the real-valued
    // cutoffs rather than rounding to integer counts is conservative at a
    // discrete boundary.
    let lower_cutoff = p - distance;
    let upper_cutoff = p + distance;
    let lower = if lower_cutoff >= 0.0 {
        (-(samples as f64) * kl(lower_cutoff, p)).exp()
    } else {
        0.0
    };
    let upper = if upper_cutoff <= 1.0 {
        (-(samples as f64) * kl(upper_cutoff, p)).exp()
    } else {
        0.0
    };
    (lower + upper).min(1.0)
}

/// IID independent output pairs coupled to a lazy uniform permutation on at
/// most q distinct inputs. Union bound on cross-pair output collisions; the
/// denominator is conservatively reduced for within-pair exclusions.
pub fn coupling_slack(q: u64) -> f64 {
    let q = q as f64;
    (q * (q - 1.0).max(0.0) / (2.0 * (2.0_f64.powi(128) - 1.0))).min(1.0)
}

pub fn corrected_bound(hits: u64, n: u64, p: f64, tests: usize, q: u64) -> f64 {
    ((tail_bound(hits, n, p) + coupling_slack(q)) * tests as f64).min(1.0)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn sparse_and_boundary_cases() {
        assert_eq!(tail_bound(0, 1, 0.0), 1.0);
        assert_eq!(tail_bound(1, 1, 0.0), 0.0);
        assert_eq!(tail_bound(0, 0, 0.5), 1.0);
        assert_eq!(tail_bound(500, 1000, 0.5), 1.0);
        assert!(tail_bound(0, 8192, 1.0 / 256.0) < 1e-5);
        assert_eq!(null_probability(128, true), 0.0);
        assert!(coupling_slack(1_000_000) < 1e-25);
        assert!(
            corrected_bound(0, 8192, 1.0 / 256.0, 100, 16384) >= tail_bound(0, 8192, 1.0 / 256.0)
        );
    }

    #[test]
    fn two_sided_bound_covers_the_opposite_tail_for_skewed_p() {
        let (n, p, hits) = (1000u64, 0.1, 50u64);
        let observed = hits as f64 / n as f64;
        let naive = (2.0 * (-(n as f64) * kl(observed, p)).exp()).min(1.0);
        let bound = tail_bound(hits, n, p);

        // Exact binomial probability of a deviation at least this large:
        // X <= 50 or X >= 150. A recurrence avoids a factorial dependency.
        let mut mass = (n as f64 * (1.0 - p).ln()).exp();
        let mut exact = 0.0;
        for k in 0..=n {
            if k <= 50 || k >= 150 {
                exact += mass;
            }
            if k < n {
                mass *= (n - k) as f64 / (k + 1) as f64 * p / (1.0 - p);
            }
        }
        assert!(naive < exact, "fixture must expose the underbound");
        assert!(
            bound >= exact,
            "{bound} must cover exact tail probability {exact}"
        );
        assert!(bound < 1.0);
    }
}
