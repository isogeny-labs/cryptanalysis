//! Standalone exact membership benchmark for canonical 31-bit integer keys.
use std::{hint::black_box, time::Instant};
const EMPTY: u32 = u32::MAX;
const MULTIPLE: u32 = EMPTY - 1;
const N: usize = 71;
const P: u32 = (1 << 31) - 1;

fn slot(key: u32) -> usize {
    (key.wrapping_mul(2654435761) >> 24) as usize
}

pub(crate) fn build(keys: &[u32]) -> [u32; 256] {
    let mut table = [EMPTY; 256];
    for &key in keys {
        let cell = &mut table[slot(key)];
        if *cell == EMPTY {
            *cell = key;
        } else if *cell != key {
            *cell = MULTIPLE;
        }
    }
    table
}

pub(crate) fn lookup(table: &[u32; 256], keys: &[u32], key: u32) -> bool {
    let entry = table[slot(key)];
    entry == key || (entry == MULTIPLE && keys.binary_search(&key).is_ok())
}

fn next(seed: &mut u64) -> u32 {
    *seed ^= *seed << 13;
    *seed ^= *seed >> 7;
    *seed ^= *seed << 17;
    (*seed % u64::from(P)) as u32
}

fn timed(mut work: impl FnMut() -> usize, repetitions: usize) -> (usize, f64) {
    let now = Instant::now();
    let mut checksum = 0;
    for _ in 0..repetitions {
        checksum += black_box(work());
    }
    (
        checksum,
        now.elapsed().as_nanos() as f64 / repetitions as f64,
    )
}

fn main() {
    let round: usize = std::env::args().nth(1).unwrap().parse().unwrap();
    let mut seed = 123456789 + round as u64;
    let mut keys = Vec::from([0, P - 1]);
    while keys.len() < N {
        let k = next(&mut seed);
        if !keys.contains(&k) {
            keys.push(k);
        }
    }
    keys.sort_unstable();
    let table = build(&keys);
    let crowded = table.iter().filter(|&&x| x == MULTIPLE).count();
    let (_, setup) = timed(
        || {
            black_box(build(black_box(&keys)));
            0
        },
        8192,
    );
    for (i, stride) in [0, 8, 1].into_iter().enumerate() {
        let queries: Vec<_> = (0..142 * 32)
            .map(|j| {
                if stride > 0 && j % stride == 0 {
                    keys[next(&mut seed) as usize % N]
                } else {
                    loop {
                        let k = next(&mut seed);
                        if !keys.contains(&k) {
                            break k;
                        }
                    }
                }
            })
            .collect();
        for &q in keys.iter().chain(&queries) {
            assert_eq!(lookup(&table, &keys, q), keys.binary_search(&q).is_ok());
        }
        let sorted = || {
            timed(
                || {
                    black_box(&queries)
                        .iter()
                        .filter(|q| black_box(&keys).binary_search(q).is_ok())
                        .count()
                },
                256,
            )
        };
        let bucket = || {
            timed(
                || {
                    black_box(&queries)
                        .iter()
                        .filter(|&&q| lookup(black_box(&table), black_box(&keys), q))
                        .count()
                },
                256,
            )
        };
        let (a, b) = if (round + i) % 2 == 0 {
            (sorted(), bucket())
        } else {
            let b = bucket();
            (sorted(), b)
        };
        assert_eq!(a.0, b.0);
        println!(
            "{round},{stride},{crowded},{setup:.3},{:.3},{:.3}",
            a.1 / 32.,
            b.1 / 32.
        );
    }
}
