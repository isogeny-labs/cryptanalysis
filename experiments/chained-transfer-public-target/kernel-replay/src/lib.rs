//! Read-only rank/truth-table/centralizer replay; frozen protocol12e924.
#![allow(dead_code)]
#[cfg(test)]
mod tests {
    use chained_original_smith_engine::original;
    use serde_json::{json, Value};
    use std::collections::HashSet;
    use std::io::Read;
    type M = [u8; 6];
    fn apply(m: &M, v: u8) -> u8 {
        (0..6).fold(0, |a, i| if v >> i & 1 == 1 { a ^ m[i] } else { a })
    }
    fn product(a: &M, b: &M) -> M {
        b.map(|v| apply(a, v))
    }
    fn form(v: u8, w: u8) -> u8 {
        (0..3).fold(0, |a, i| {
            a ^ (((v >> (2 * i)) & 1) & ((w >> (2 * i + 1)) & 1))
                ^ (((v >> (2 * i + 1)) & 1) & ((w >> (2 * i)) & 1))
        })
    }
    fn quadratic(v: u8) -> u8 {
        (0..3).fold(0, |a, i| {
            a ^ (((v >> (2 * i)) & 1) & ((v >> (2 * i + 1)) & 1))
        })
    }
    fn rank(columns: M) -> usize {
        let mut rows = columns;
        let mut pivot = 0;
        for bit in (0..6).rev() {
            if let Some(i) = (pivot..6).find(|&i| rows[i] & (1 << bit) != 0) {
                rows.swap(pivot, i);
                for j in 0..6 {
                    if j != pivot && rows[j] & (1 << bit) != 0 {
                        rows[j] ^= rows[pivot];
                    }
                }
                pivot += 1;
            }
        }
        pivot
    }
    fn odd_truth_tables() -> Vec<u64> {
        let mut out = vec![];
        for beta in 0..64u8 {
            if quadratic(beta) == 0 {
                continue;
            }
            let mut table = 0u64;
            for x in 0..64u8 {
                let linear = (0..6).fold(0u8, |a, i| a ^ (((beta >> i) & 1) & ((x >> i) & 1)));
                table |= ((quadratic(x) ^ linear) as u64) << x;
            }
            out.push(table);
        }
        assert_eq!(out.len(), 28);
        out
    }
    fn fixed_odd(m: &M, tables: &[u64]) -> usize {
        tables
            .iter()
            .filter(|&&table| (0..6).all(|i| ((table >> m[i]) & 1) == ((table >> (1 << i)) & 1)))
            .count()
    }
    fn fixed_perm(perm: &[usize], n: usize) -> usize {
        (0..perm.len())
            .filter(|&i| {
                let mut at = i;
                for _ in 0..n {
                    at = perm[at];
                }
                at == i
            })
            .count()
    }
    fn symplectic(m: &M) {
        for i in 0..6 {
            for j in 0..6 {
                assert_eq!(
                    form(m[i], m[j]),
                    if i / 2 == j / 2 && i != j { 1 } else { 0 }
                );
            }
        }
    }
    fn abstract_representative() -> (M, (u32, u32)) {
        let basis = [3u8, 5, 15, 23, 63, 95];
        let mut inverse = [255u8; 128];
        let mask: [u8; 64] = std::array::from_fn(|v| apply(&basis, v as u8));
        for i in 0..64 {
            assert_eq!(inverse[mask[i] as usize], 255);
            inverse[mask[i] as usize] = i as u8;
        }
        for a in 0..64u8 {
            for b in 0..64u8 {
                assert_eq!(
                    form(a, b) as u32,
                    (mask[a as usize] & mask[b as usize]).count_ones() % 2
                );
            }
        }
        let perm = original::perm_of_type(&[6, 1, 1]);
        let matrix = basis.map(|v| {
            let mut next = 0u8;
            for bit in 0..8 {
                if v >> bit & 1 == 1 {
                    next |= 1 << perm[bit];
                }
            }
            if next & 128 != 0 {
                next ^= 255;
            }
            inverse[next as usize]
        });
        symplectic(&matrix);
        let counts = original::stable_kernels(&perm, &original::lagrangians());
        (matrix, counts)
    }
    #[test]
    fn read_every_saved_matrix_and_recover_conjugacy_by_commuting_count() {
        let input: Value = serde_json::from_str(include_str!(
            "../../kernel-census/fixtures/actual-frobenius.json"
        ))
        .unwrap();
        let perm: Vec<usize> = input["native_bitangent_frobenius"]["permutation"]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| x.as_u64().unwrap() as usize)
            .collect();
        assert_eq!(perm.len(), 28);
        assert!(perm.iter().all(|&i| i < 28));
        let expected_fixed: [usize; 3] = [1, 2, 3].map(|n| fixed_perm(&perm, n));
        let orders = input["native_two_primary_group"]["exact_orders"]
            .as_array()
            .unwrap();
        let rational_fixed = orders
            .iter()
            .filter(|x| 2 % x.as_u64().unwrap() == 0)
            .count();
        let tables = odd_truth_tables();
        let identity: M = std::array::from_fn(|i| 1 << i);
        assert_eq!(fixed_odd(&identity, &tables), 28);
        let mut transvection = identity;
        transvection[1] ^= 1;
        assert_eq!(fixed_odd(&transvection, &tables), 16);
        let (representative, original_counts) = abstract_representative();
        assert_eq!(
            [
                representative,
                product(&representative, &representative),
                product(&product(&representative, &representative), &representative)
            ]
            .map(|m| fixed_odd(&m, &tables)),
            expected_fixed
        );
        let path =
            std::env::var_os("N4_KERNEL_CENSUS_IN").expect("explicit frozen binary input required");
        let mut raw = vec![];
        std::fs::File::open(path)
            .unwrap()
            .read_to_end(&mut raw)
            .unwrap();
        assert_eq!(&raw[..8], b"CTSP6V1\n");
        assert_eq!((raw.len() - 8) % 9, 0);
        let mut seen = HashSet::with_capacity(1_451_520);
        let mut compatible = 0usize;
        let mut commuting = 0usize;
        for row in raw[8..].chunks_exact(9) {
            let code = u64::from_le_bytes(row[..8].try_into().unwrap());
            assert_eq!(code >> 36, 0);
            assert!(seen.insert(code));
            let matrix: M = std::array::from_fn(|i| ((code >> (6 * i)) & 63) as u8);
            symplectic(&matrix);
            if product(&matrix, &representative) == product(&representative, &matrix) {
                commuting += 1;
            }
            let difference = std::array::from_fn(|i| matrix[i] ^ (1 << i));
            let fixed = 1usize << (6 - rank(difference));
            let squared = product(&matrix, &matrix);
            let cubed = product(&squared, &matrix);
            let sixth = product(&cubed, &cubed);
            let accepted = fixed == rational_fixed
                && sixth == identity
                && [matrix, squared, cubed].map(|m| fixed_odd(&m, &tables)) == expected_fixed;
            if accepted {
                compatible += 1;
                assert_eq!(row[8], original_counts.1 as u8);
            } else {
                assert_eq!(row[8], 255);
            }
        }
        assert_eq!(seen.len(), 1_451_520);
        assert!(commuting > 0);
        assert_eq!(seen.len() % commuting, 0);
        let conjugacy_class = seen.len() / commuting;
        assert_eq!(compatible, conjugacy_class);
        println!(
            "N4_KERNEL_REPLAY_INPUT {}",
            json!({"raw_schema":"CTSP6V1/9byteallmatrixrows","raw_bytes":raw.len(),"actual_fixed_vectors":rational_fixed,"actual_odd_fixed_F_F2_F3":expected_fixed,"literal_actual_odd_permutation":perm})
        );
        println!(
            "N4_KERNEL_REPLAY_CONTROLS {}",
            json!({"identity_fixed_odd":28,"transvection_fixed_odd":16,"original_S8_representative_pair_any":original_counts,"explicit_basis4096_pairings":true,"predicate_method":"Gaussianrank plus quadratic truth-table fixedforms ofthreepowers andM6identity"})
        );
        println!(
            "N4_KERNEL_REPLAY_FULL {}",
            json!({"all_distinct_symplectic_matrices_replayed":seen.len(),"actual_compatible_actions":compatible,"representative_centralizer":commuting,"group_order_divided_by_centralizer":conjugacy_class,"compatible_card_equals_single_conjugacy_class":true,"all_producer_predicate_and_count_bytes_match":true,"representative_stable_kernel_count":original_counts.1,"every_raw_record_read":true})
        );
        println!(
            "N4_KERNEL_REPLAY_SCOPE {}",
            json!({"scope":"differentrank/truthpowers/commutant algorithm,nottrustedproducer-independentexecutionbackend;standardgroupcardinality/conjugacyinvariance/theta/Frobenius/quotientbridgeswritten;actualNormkernelmembershipmustbeauditedbeforefixeddegreeobstruction","noactualkernelcoordinates_or_newmap_or_costclaim":true})
        );
    }
}
