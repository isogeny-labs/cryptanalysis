use crate::ec::Group;
use crate::{need, AResult};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct C(pub [i64; 2]);
pub const fn c(a: i64, b: i64) -> C { C([a, b]) }
pub const Z: C = c(0, 0);
pub const I: C = c(1, 0);
pub type Matrix = [[C; 3]; 3];
pub const H: Matrix = [
    [c(2, 0), I, c(-1, 0)],
    [I, c(3, 0), c(-2, 1)],
    [c(-1, 0), c(-1, -1), c(3, 0)],
];
pub const HI: Matrix = [
    [c(2, 0), c(-2, 1), c(1, 1)],
    [c(-1, -1), c(5, 0), c(3, -2)],
    [c(2, -1), c(1, 2), c(5, 0)],
];
pub const S: Matrix = [
    [c(-4, 0), c(-2, 0), c(2, 0)],
    [c(2, 2), c(-1, 2), c(-1, -2)],
    [c(-4, 2), c(-3, 1), c(3, -1)],
];
pub const R: Matrix = [
    [c(-3, 1), Z, c(2, 0)],
    [c(4, 0), c(-2, 0), c(0, -2)],
    [c(0, 2), c(-2, 0), c(4, -2)],
];
pub const T: Matrix = [
    [I, I, Z],
    [c(-1, -1), Z, c(-1, 0)],
    [c(2, -1), Z, c(-1, 0)],
];
const N: Matrix = [
    [Z, c(-1, 0), I],
    [c(3, 0), I, c(-1, 0)],
    [Z, c(-2, 1), c(-1, -1)],
];

impl C {
    pub fn plus(self, rhs: Self) -> Self {
        Self(std::array::from_fn(|i| self.0[i] + rhs.0[i]))
    }
    pub fn neg(self) -> Self { Self(self.0.map(|x| -x)) }
    pub fn times(self, rhs: Self) -> Self {
        let mut polynomial = [0_i64; 3];
        for (i, &a) in self.0.iter().enumerate() {
            for (j, &b) in rhs.0.iter().enumerate() {
                polynomial[i + j] += a * b;
            }
        }
        // Long reduction by w^2-w+5, independently of finite-point actions.
        polynomial[0] -= 5 * polynomial[2];
        polynomial[1] += polynomial[2];
        Self([polynomial[0], polynomial[1]])
    }
    pub fn bar(self) -> Self { c(self.0[0] + self.0[1], -self.0[1]) }
}
pub fn matrix(a: Matrix, b: Matrix) -> Matrix {
    std::array::from_fn(|i| std::array::from_fn(|j| {
        (0..3).fold(Z, |sum, k| sum.plus(a[i][k].times(b[k][j])))
    }))
}
pub fn dagger(a: Matrix) -> Matrix {
    std::array::from_fn(|i| std::array::from_fn(|j| a[j][i].bar()))
}
fn identity(scale: i64) -> Matrix {
    std::array::from_fn(|i| std::array::from_fn(|j| if i == j { c(scale, 0) } else { Z }))
}
fn scaled(a: Matrix, n: i64) -> Matrix { a.map(|row| row.map(|x| x.times(c(n, 0)))) }
fn determinant(a: Matrix) -> C {
    let mut value = Z;
    for (permutation, sign) in [([0,1,2],1),([1,2,0],1),([2,0,1],1),([0,2,1],-1),([1,0,2],-1),([2,1,0],-1)] {
        value = value.plus((0..3).fold(c(sign,0), |term, row| term.times(a[row][permutation[row]])));
    }
    value
}
fn column(a: Matrix, v: [C; 3]) -> [C; 3] {
    a.map(|row| row.into_iter().zip(v).fold(Z, |s, (x,y)| s.plus(x.times(y))))
}
fn row(v: [C; 3], a: Matrix) -> [C; 3] {
    std::array::from_fn(|j| (0..3).fold(Z, |s, i| s.plus(v[i].times(a[i][j]))))
}
fn dot(a: [C; 3], b: [C; 3]) -> C {
    a.into_iter().zip(b).fold(Z, |s, (x,y)| s.plus(x.times(y)))
}
fn similitude(a: Matrix, h: Matrix) -> bool {
    matrix(matrix(dagger(a), h), a) == scaled(h, 4)
}

pub fn qualify() -> AResult<()> {
    need(dagger(H) == H && determinant(H) == I, "fixed Hermitian H")?;
    need(matrix(H,HI) == identity(1) && matrix(HI,H) == identity(1), "fixed H inverse")?;
    need(similitude(S,H) && similitude(R,H), "actual CM four similitudes")?;
    need(R == matrix(matrix(HI,dagger(S)),H), "integral Rosati adjoint")?;
    need(matrix(R,S) == identity(4) && matrix(S,R) == identity(4), "global CM composites")?;
    let determinant = determinant(S);
    need(determinant == c(8,0) && determinant.times(determinant.bar()) == c(64,0), "CM determinant norm64")?;
    need(matrix(N,T) == identity(3) && matrix(T,N) == identity(3), "genuine cover-basis integer relation")?;
    let v = T.map(|entry| entry[0]);
    let u = column(S,v);
    let ell = [c(0,1),I,Z];
    need(u == [c(2,0),c(1,-2),c(5,-1)], "written transfer column")?;
    need(dot(ell,u) == I, "global integral left inverse coefficient identity")?;
    let ell_hi = row(ell,HI);
    need(ell_hi == [c(-1,1),c(0,-1),c(-2,0)], "written inverse Gram row")?;
    need(dot(ell_hi,ell.map(C::bar)) == c(4,0), "degree4 norm coefficient identity")?;
    need(row(ell_hi,dagger(N)) == [c(-2,1),c(-1,2),c(-1,0)], "three times L actual pushforward row")?;
    let mut wrong_s = S;wrong_s[0][0] = wrong_s[0][0].plus(I);
    let mut wrong_h = H;wrong_h[0][0] = wrong_h[0][0].plus(I);
    need(!similitude(wrong_s,H) && !similitude(S,wrong_h), "changed actual CM coefficients rejected")?;
    need(similitude(S,H), "pristine CM restored")?;
    println!("CM_WRITTEN_IDENTITIES\tRS=SR=4I\tnormdet=64\tSv=u\tell*u=1\tellHinvell*=4\tthreeL_pushforward\tmutations_reject_restore\tPASS");
    Ok(())
}

pub struct Action { table: [[Vec<usize>; 3]; 3] }
impl Action {
    pub fn new(coefficients: Matrix, g: &Group) -> AResult<Self> {
        let table: [[Vec<usize>; 3]; 3] = coefficients.map(|row| row.map(|coefficient| {
            (0..g.points.len()).map(|p| g.cm(p,coefficient.0)).collect()
        }));
        for row in &table {
            for action in row {
                for p in 0..g.points.len() {
                    for q in 0..g.points.len() {
                        need(action[g.plus[p][q]] == g.plus[action[p]][action[q]], "new-model CM action homomorphism")?;
                    }
                }
            }
        }
        Ok(Self { table })
    }
    pub fn apply(&self, g: &Group, point: [usize;3]) -> [usize;3] {
        self.table.each_ref().map(|row| row.iter().zip(point).fold(0,|sum,(entry,p)| g.plus[sum][entry[p]]))
    }
}
pub fn encode(point: [usize;3], n: usize) -> usize { point[0]+n*point[1]+n*n*point[2] }
pub fn decode(mut index: usize, n: usize) -> [usize;3] {
    assert!(index<n*n*n);
    std::array::from_fn(|_| { let digit=index%n;index/=n;digit })
}
