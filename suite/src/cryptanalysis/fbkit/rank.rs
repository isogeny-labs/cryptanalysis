//! Ranking of measured cells (spec section 5): single objectives, a weighted
//! geometric-mean composite normalised to the best cell of the sweep, the
//! Pareto front and the per-family best.
//!
//! Ranking is a stage diagnostic over this sweep only. It is not an `IC1`
//! result and not a speedup: the objectives are costs of a Weil-descent
//! solver stage and of relation yield, nothing end to end.

use std::collections::BTreeMap;
use std::fmt::Write as _;

use serde::Serialize;
use serde_json::{json, Value};

use super::{CellRecord, RANKING_SCHEMA};

/// What to minimise.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum Objective {
    /// `derived.expected_pdp_ops`.
    ExpectedOps,
    /// Random-class mean Macaulay solving degree, then its maximum.
    SolvingDegree,
    /// SAT clause count.
    SatClauses,
    /// Random-class mean SAT conflicts.
    SatConflicts,
    /// Effective columns.
    Columns,
    /// Weighted geometric mean of the normalised components.
    Composite,
}

impl Objective {
    /// Parse the `--objective` value.
    pub fn parse(s: &str) -> Result<Self, String> {
        Ok(match s.trim() {
            "expected-ops" => Self::ExpectedOps,
            "solving-degree" => Self::SolvingDegree,
            "sat-clauses" => Self::SatClauses,
            "sat-conflicts" => Self::SatConflicts,
            "columns" => Self::Columns,
            "composite" => Self::Composite,
            other => {
                return Err(format!(
                    "unknown objective `{other}`; try expected-ops, solving-degree, sat-clauses, sat-conflicts, columns or composite"
                ))
            }
        })
    }

    /// The spelling accepted by [`Objective::parse`].
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ExpectedOps => "expected-ops",
            Self::SolvingDegree => "solving-degree",
            Self::SatClauses => "sat-clauses",
            Self::SatConflicts => "sat-conflicts",
            Self::Columns => "columns",
            Self::Composite => "composite",
        }
    }
}

/// Composite weights (`--weights ops=1,dreg=1,clauses=0.5,conflicts=0.5,columns=0.5`).
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct Weights {
    /// `expected_pdp_ops`.
    pub ops: f64,
    /// `solving_degree_mean`.
    pub dreg: f64,
    /// SAT clauses.
    pub clauses: f64,
    /// SAT conflicts mean.
    pub conflicts: f64,
    /// Effective columns.
    pub columns: f64,
}

impl Default for Weights {
    fn default() -> Self {
        Self {
            ops: 1.0,
            dreg: 1.0,
            clauses: 0.5,
            conflicts: 0.5,
            columns: 0.5,
        }
    }
}

impl Weights {
    /// Parse `k=v,k=v` over the defaults.
    pub fn parse(s: &str) -> Result<Self, String> {
        let mut w = Self::default();
        for item in s.split(',').filter(|p| !p.trim().is_empty()) {
            let (k, v) = item
                .split_once('=')
                .ok_or_else(|| format!("weight `{item}` is not key=value"))?;
            let v: f64 = v
                .trim()
                .parse()
                .map_err(|_| format!("weight `{item}` is not a number"))?;
            if !(v >= 0.0 && v.is_finite()) {
                return Err(format!("weight `{item}` must be a non-negative number"));
            }
            match k.trim() {
                "ops" => w.ops = v,
                "dreg" => w.dreg = v,
                "clauses" => w.clauses = v,
                "conflicts" => w.conflicts = v,
                "columns" => w.columns = v,
                other => return Err(format!("unknown weight `{other}`")),
            }
        }
        Ok(w)
    }
}

/// The numbers a ranking reads from a cell; `None` is unmeasured.
#[derive(Debug, Clone, Copy, Default, PartialEq, Serialize)]
pub struct Figures {
    /// `yield.expected_trials`.
    pub expected_trials: Option<f64>,
    /// `derived.expected_pdp_ops`.
    pub expected_ops: Option<f64>,
    /// Random-class mean solving degree.
    pub dreg_mean: Option<f64>,
    /// Random-class maximum solving degree.
    pub dreg_max: Option<f64>,
    /// SAT clauses.
    pub clauses: Option<f64>,
    /// Random-class mean conflicts.
    pub conflicts: Option<f64>,
    /// Effective columns.
    pub columns: Option<f64>,
}

impl Figures {
    /// Read the figures of a cell record.
    pub fn of(c: &CellRecord) -> Self {
        let num = |v: &Value| v.as_f64();
        let m = &c.metrics;
        Self {
            expected_trials: num(&m["yield"]["expected_trials"]),
            expected_ops: num(&m["derived"]["expected_pdp_ops"]),
            dreg_mean: num(&m["f4"]["random"]["solving_degree_mean"]),
            dreg_max: num(&m["f4"]["random"]["solving_degree_max"]),
            clauses: num(&m["sat"]["clauses"]),
            conflicts: num(&m["sat"]["random"]["conflicts_mean"]),
            columns: num(&m["construction"]["effective_columns"]),
        }
    }
}

/// One ranked cell.
#[derive(Debug, Clone, Serialize)]
pub struct RankedCell {
    /// 1-based position.
    pub rank: usize,
    /// Cell ID.
    pub cell_id: String,
    /// Family.
    pub family: String,
    /// Summand count.
    pub m: u32,
    /// The objective value (the composite is dimensionless, 1 is best).
    pub value: f64,
    /// Figures the ranking read.
    pub figures: Figures,
}

/// The result of [`rank`].
#[derive(Debug, Clone, Serialize)]
pub struct Ranking {
    /// `ic-fbkit-ranking/1`.
    pub schema: String,
    /// Objective used.
    pub objective: Objective,
    /// Composite weights (used by the composite only).
    pub weights: Weights,
    /// Ranked cells, best first.
    pub ordered: Vec<RankedCell>,
    /// Cells with a null objective, with the reason, listed after the ranked.
    pub unranked_with_reason: Vec<(String, String)>,
    /// Non-dominated cell IDs.
    pub pareto_front: Vec<String>,
    /// Axes the front was computed over.
    pub pareto_axes: Vec<String>,
    /// Best ranked cell per family.
    pub per_family_best: BTreeMap<String, String>,
    /// Markdown table of the top ten, the front and the per-family best.
    pub markdown: String,
}

impl Ranking {
    /// The ranking as the `ranking.json` document.
    pub fn to_json(&self) -> Value {
        let mut v = serde_json::to_value(self).unwrap_or(Value::Null);
        if let Some(o) = v.as_object_mut() {
            o.insert(
                "what_this_is".into(),
                json!("an ordering of factor-base cells of one sweep under one stage objective"),
            );
            o.insert(
                "what_this_is_not".into(),
                json!("an IC1 result or a speedup; solver and yield numbers are stage diagnostics"),
            );
        }
        v
    }

    /// Render the top `top` rows, the front and the per-family best.
    pub fn render(&self, top: usize) -> String {
        let mut s = String::new();
        let _ = writeln!(
            s,
            "Ranking by `{}` (lower is better; a stage diagnostic, not an IC1 result or a speedup)\n",
            self.objective.as_str()
        );
        let _ = writeln!(
            s,
            "| # | cell | family | m | value | E[trials] | D mean | clauses | columns |"
        );
        let _ = writeln!(s, "|---|---|---|---|---|---|---|---|---|");
        let f = |x: Option<f64>| x.map_or("null".to_string(), |v| format!("{v:.4}"));
        for r in self.ordered.iter().take(top) {
            let _ = writeln!(
                s,
                "| {} | {} | {} | {} | {:.4} | {} | {} | {} | {} |",
                r.rank,
                r.cell_id,
                r.family,
                r.m,
                r.value,
                f(r.figures.expected_trials),
                f(r.figures.dreg_mean),
                f(r.figures.clauses),
                f(r.figures.columns)
            );
        }
        let _ = writeln!(
            s,
            "\nPareto front over ({}): {}",
            self.pareto_axes.join(", "),
            if self.pareto_front.is_empty() {
                "empty".to_string()
            } else {
                self.pareto_front.join(", ")
            }
        );
        let _ = writeln!(s, "\nBest per family:");
        for (fam, id) in &self.per_family_best {
            let _ = writeln!(s, "- {fam}: {id}");
        }
        if !self.unranked_with_reason.is_empty() {
            let _ = writeln!(s, "\nUnranked ({}):", self.unranked_with_reason.len());
            for (id, why) in self.unranked_with_reason.iter().take(top) {
                let _ = writeln!(s, "- {id}: {why}");
            }
        }
        s
    }
}

fn missing(c: &CellRecord, what: &str) -> String {
    match &c.reason {
        Some(r) if c.status != "complete" => format!("status {}: {r}", c.status),
        _ => format!("{what} not measured"),
    }
}

/// Rank `cells` under `objective`.
pub fn rank(cells: &[CellRecord], objective: Objective, weights: &Weights) -> Ranking {
    let figs: Vec<Figures> = cells.iter().map(Figures::of).collect();
    // Composite normalisers: the best (smallest positive-or-zero) value per component.
    let best = |get: &dyn Fn(&Figures) -> Option<f64>| -> Option<f64> {
        figs.iter().filter_map(get).reduce(f64::min)
    };
    let comps: [(&str, f64, Box<dyn Fn(&Figures) -> Option<f64>>); 5] = [
        (
            "expected_pdp_ops",
            weights.ops,
            Box::new(|f| f.expected_ops),
        ),
        (
            "solving_degree_mean",
            weights.dreg,
            Box::new(|f| f.dreg_mean),
        ),
        ("sat_clauses", weights.clauses, Box::new(|f| f.clauses)),
        (
            "sat_conflicts_mean",
            weights.conflicts,
            Box::new(|f| f.conflicts),
        ),
        (
            "effective_columns",
            weights.columns,
            Box::new(|f| f.columns),
        ),
    ];
    let bests: Vec<Option<f64>> = comps.iter().map(|(_, _, g)| best(g.as_ref())).collect();
    let mut ranked: Vec<(usize, f64, f64)> = Vec::new(); // (index, value, tie-break)
    let mut unranked = Vec::new();
    for (i, (c, f)) in cells.iter().zip(&figs).enumerate() {
        let scored: Result<(f64, f64), String> = match objective {
            Objective::ExpectedOps => f
                .expected_ops
                .map(|v| (v, 0.0))
                .ok_or_else(|| missing(c, "expected_pdp_ops")),
            Objective::SolvingDegree => f
                .dreg_mean
                .map(|v| (v, f.dreg_max.unwrap_or(v)))
                .ok_or_else(|| missing(c, "solving_degree_mean")),
            Objective::SatClauses => f
                .clauses
                .map(|v| (v, 0.0))
                .ok_or_else(|| missing(c, "sat clauses")),
            Objective::SatConflicts => f
                .conflicts
                .map(|v| (v, 0.0))
                .ok_or_else(|| missing(c, "sat conflicts")),
            Objective::Columns => f
                .columns
                .map(|v| (v, 0.0))
                .ok_or_else(|| missing(c, "effective_columns")),
            Objective::Composite => {
                let (mut sum, mut wsum) = (0.0, 0.0);
                let mut err = None;
                for ((name, w, get), b) in comps.iter().zip(&bests) {
                    if *w <= 0.0 {
                        continue;
                    }
                    match (get(f), b) {
                        (Some(v), Some(b)) => {
                            sum += w * ((v + 1e-9) / (b + 1e-9)).ln();
                            wsum += w;
                        }
                        _ => {
                            err = Some(missing(c, name));
                            break;
                        }
                    }
                }
                match err {
                    Some(e) => Err(e),
                    None if wsum > 0.0 => Ok(((sum / wsum).exp(), 0.0)),
                    None => Err("all composite weights are zero".into()),
                }
            }
        };
        match scored {
            Ok((v, t)) => ranked.push((i, v, t)),
            Err(why) => unranked.push((c.cell_id.clone(), why)),
        }
    }
    ranked.sort_by(|a, b| {
        a.1.total_cmp(&b.1)
            .then(a.2.total_cmp(&b.2))
            .then_with(|| cells[a.0].cell_id.cmp(&cells[b.0].cell_id))
    });
    let ordered: Vec<RankedCell> = ranked
        .iter()
        .enumerate()
        .map(|(k, &(i, v, _))| RankedCell {
            rank: k + 1,
            cell_id: cells[i].cell_id.clone(),
            family: cells[i].family.clone(),
            m: cells[i].m,
            value: v,
            figures: figs[i],
        })
        .collect();
    let mut per_family_best = BTreeMap::new();
    for r in &ordered {
        per_family_best
            .entry(r.family.clone())
            .or_insert_with(|| r.cell_id.clone());
    }
    // Pareto front over the axes every ranked-or-measured cell has.
    let axes: [(&str, Box<dyn Fn(&Figures) -> Option<f64>>); 4] = [
        ("expected_trials", Box::new(|f| f.expected_trials)),
        ("solving_degree_mean", Box::new(|f| f.dreg_mean)),
        ("clauses", Box::new(|f| f.clauses)),
        ("effective_columns", Box::new(|f| f.columns)),
    ];
    let candidates: Vec<usize> = (0..cells.len())
        .filter(|&i| matches!(cells[i].status.as_str(), "complete" | "caps_hit" | "budget"))
        .collect();
    let used: Vec<&(&str, Box<dyn Fn(&Figures) -> Option<f64>>)> = axes
        .iter()
        .filter(|(_, g)| {
            !candidates.is_empty() && candidates.iter().all(|&i| g(&figs[i]).is_some())
        })
        .collect();
    let pts: Vec<(usize, Vec<f64>)> = candidates
        .iter()
        .map(|&i| (i, used.iter().filter_map(|(_, g)| g(&figs[i])).collect()))
        .collect();
    let mut front: Vec<String> = Vec::new();
    if !used.is_empty() {
        for (i, p) in &pts {
            let dominated = pts.iter().any(|(j, q)| {
                j != i
                    && q.iter().zip(p).all(|(a, b)| a <= b)
                    && q.iter().zip(p).any(|(a, b)| a < b)
            });
            if !dominated {
                front.push(cells[*i].cell_id.clone());
            }
        }
    }
    let mut ranking = Ranking {
        schema: RANKING_SCHEMA.into(),
        objective,
        weights: *weights,
        ordered,
        unranked_with_reason: unranked,
        pareto_front: front,
        pareto_axes: used.iter().map(|(n, _)| (*n).to_string()).collect(),
        per_family_best,
        markdown: String::new(),
    };
    ranking.markdown = ranking.render(10);
    ranking
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::fbkit::CELL_SCHEMA;

    fn cell(
        id: &str,
        fam: &str,
        trials: f64,
        d: f64,
        clauses: f64,
        cols: f64,
        ops: Option<f64>,
    ) -> CellRecord {
        CellRecord {
            schema: CELL_SCHEMA.into(),
            cell_id: id.into(),
            curve_id: "c".into(),
            family: fam.into(),
            recipe: json!({}),
            m: 2,
            status: "complete".into(),
            reason: None,
            metrics: json!({
                "yield": {"expected_trials": trials},
                "f4": {"random": {"solving_degree_mean": d, "solving_degree_max": d + 1.0}},
                "sat": {"clauses": clauses, "random": {"conflicts_mean": d * 10.0}},
                "construction": {"effective_columns": cols},
                "derived": {"expected_pdp_ops": ops},
            }),
            ps1_label: None,
            point_set_sha256: None,
            factor_base_sha256: None,
            elapsed_seconds: 0.0,
        }
    }

    fn sample() -> Vec<CellRecord> {
        vec![
            cell("a", "coordinate", 100.0, 4.0, 500.0, 50.0, Some(1e6)),
            cell("b", "random", 50.0, 5.0, 600.0, 60.0, Some(2e6)),
            cell("c", "geometric", 200.0, 4.0, 700.0, 70.0, Some(5e5)),
            cell("d", "random", 300.0, 6.0, 800.0, 80.0, None),
        ]
    }

    #[test]
    fn objectives_order_and_unranked() {
        let w = Weights::default();
        let r = rank(&sample(), Objective::ExpectedOps, &w);
        let ids: Vec<&str> = r.ordered.iter().map(|c| c.cell_id.as_str()).collect();
        assert_eq!(ids, ["c", "a", "b"]);
        assert_eq!(r.unranked_with_reason.len(), 1);
        assert_eq!(r.unranked_with_reason[0].0, "d");
        let r = rank(&sample(), Objective::SolvingDegree, &w);
        assert_eq!(
            r.ordered[0].cell_id, "a",
            "tie on mean broken by max then id"
        );
        let r = rank(&sample(), Objective::Columns, &w);
        assert_eq!(r.ordered.len(), 4);
        assert_eq!(r.per_family_best["random"], "b");
    }

    #[test]
    fn composite_is_one_for_a_dominating_cell() {
        let mut cells = sample();
        cells.push(cell("best", "x", 1.0, 1.0, 1.0, 1.0, Some(1.0)));
        let r = rank(&cells, Objective::Composite, &Weights::default());
        assert_eq!(r.ordered[0].cell_id, "best");
        assert!((r.ordered[0].value - 1.0).abs() < 1e-6);
        assert!(r.unranked_with_reason.iter().any(|(id, _)| id == "d"));
        assert!(r.markdown.contains("not an IC1 result"));
    }

    #[test]
    fn pareto_front_and_weights() {
        let r = rank(&sample(), Objective::Columns, &Weights::default());
        // d is dominated by a on every axis; b trades trials for the rest.
        assert!(r.pareto_front.contains(&"b".to_string()));
        assert!(r.pareto_front.contains(&"a".to_string()));
        assert!(!r.pareto_front.contains(&"d".to_string()));
        assert_eq!(r.pareto_axes.len(), 4);
        let w = Weights::parse("ops=2,columns=0").expect("weights");
        assert_eq!((w.ops, w.columns, w.dreg), (2.0, 0.0, 1.0));
        assert!(Weights::parse("zzz=1").is_err());
        assert_eq!(
            Objective::parse("sat-clauses").expect("obj"),
            Objective::SatClauses
        );
        assert!(Objective::parse("nope").is_err());
        assert_eq!(r.to_json()["schema"], json!(RANKING_SCHEMA));
    }
}
