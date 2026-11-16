//! Third method: enumerate actual finite solution sets directly, without using
//! either implementation's kernel basis to construct the expected projection.
use chained_transfer_lp_finite_projection_01::{development, projection, Matrix};

fn decode(mut code: usize, width: usize) -> Vec<u64> {
    let mut vector = Vec::with_capacity(width);
    for _ in 0..width {
        vector.push((code % 101) as u64);
        code /= 101;
    }
    vector
}

fn all_rows_zero(matrix: &Matrix, vector: &[u64]) -> bool {
    assert_eq!(matrix.ncols, vector.len());
    assert!(matrix.ncols <= 3);
    matrix.rows.iter().all(|row| {
        assert_eq!(row.len(), vector.len());
        // At most three canonical F101 products: ordinary u64 sum is exact.
        row.iter().zip(vector).map(|(&a, &b)| a * b).sum::<u64>() % 101 == 0
    })
}

fn compare_entire_sets(full: &Matrix, lp: usize) {
    assert!(full.ncols <= 3 && lp <= full.ncols);
    let fb = full.ncols - lp;
    let empty = Matrix {
        ncols: fb,
        rows: vec![],
    };
    let certificate = projection::produce(101, full, lp, &empty, &empty).unwrap();
    projection::verify(101, full, lp, &empty, &empty, &certificate).unwrap();
    let full_count = 101_usize.pow(full.ncols as u32);
    let fb_count = 101_usize.pow(fb as u32);
    let lp_radix = 101_usize.pow(lp as u32);
    let mut actually_projected = vec![false; fb_count];
    for encoded in 0..full_count {
        let vector = decode(encoded, full.ncols);
        if all_rows_zero(full, &vector) {
            actually_projected[encoded / lp_radix] = true;
        }
    }
    for (encoded, &present) in actually_projected.iter().enumerate() {
        let vector = decode(encoded, fb);
        assert_eq!(
            present,
            all_rows_zero(&certificate.c.input, &vector),
            "complete finite projection differs at {vector:?}"
        );
    }
    println!("exhaustive full vectors={full_count}, projected candidates={fb_count}, LPcolumns={lp}, FBcolumns={fb}: complete sets equal");
}

#[test]
fn exhaustive_tractable_declared_fixtures() {
    for case in development::cases()
        .into_iter()
        .filter(|c| c.full.ncols <= 3)
    {
        println!("fixture {}", case.name);
        compare_entire_sets(&case.full, case.lp_columns);
    }
}

#[test]
fn exhaustive_repeated_ground_and_half_ground() {
    for coefficient in [1, 2] {
        let full = Matrix {
            ncols: 3,
            rows: vec![vec![coefficient, 1, 0], vec![1, 0, 1]],
        };
        println!("two grounds, first LP coefficient={coefficient}");
        compare_entire_sets(&full, 1);
    }
}
