//! Access adapter to ORIGINAL normalized SevenEdge construction/evaluation.
//! Normal dependency compilation leaves its original tests in the old jobs.
#[allow(dead_code, unused_imports)]
#[path = "../../../src/seven.rs"]
mod original_seven;

use isogeny_algos::curve::{self, Curve, Isogeny, Pt};
use isogeny_algos::field::Zp;
type Result<T> = std::result::Result<T, String>;

pub struct Alpha49 {
    field: Zp,
    first: original_seven::SevenEdge,
    second: original_seven::SevenEdge,
}
impl Alpha49 {
    pub fn new() -> Result<Self> {
        let field = Zp::new(101);
        let source = Curve::new(1, 46);
        let middle = Curve::new(26, 58);
        let target = Curve::new(59, 27);
        let unique = |from: Curve<u64>, to: Curve<u64>| {
            let mut edges = original_seven::construct_edges(&field, &from)
                .into_iter()
                .filter(|edge| edge.map.cod == to);
            let edge = edges.next().ok_or("fixed normalized7 edge missing")?;
            if edges.next().is_some() {
                return Err("ambiguous fixed normalized7 edge");
            }
            Ok(edge)
        };
        Ok(Self {
            field,
            first: unique(source, middle)?,
            second: unique(middle, target)?,
        })
    }
    fn admit(&self, curve: Curve<u64>, point: &Pt<u64>) -> Result<()> {
        if let Pt::Aff(x, y) = *point {
            if x >= 101 || y >= 101 || !curve::on_curve(&self.field, &curve, point) {
                return Err("noncanonical/off-curve alpha49 input".into());
            }
        }
        Ok(())
    }
    pub fn forward(&self, point: &Pt<u64>) -> Result<Pt<u64>> {
        self.admit(self.first.map.dom, point)?;
        let out = self
            .second
            .map
            .eval(&self.field, &self.first.map.eval(&self.field, point));
        self.admit(self.second.map.cod, &out)?;
        Ok(out)
    }
    pub fn reverse(&self, point: &Pt<u64>) -> Result<Pt<u64>> {
        self.admit(self.second.map.cod, point)?;
        let out = self
            .first
            .reverse(&self.field, &self.second.reverse(&self.field, point));
        self.admit(self.first.map.dom, &out)?;
        Ok(out)
    }
    /// Validation control:actual backtrack through the first edge,ending on E0.
    pub fn first_roundtrip_control(&self, point: &Pt<u64>) -> Result<Pt<u64>> {
        self.admit(self.first.map.dom, point)?;
        Ok(self
            .first
            .reverse(&self.field, &self.first.map.eval(&self.field, point)))
    }
}
