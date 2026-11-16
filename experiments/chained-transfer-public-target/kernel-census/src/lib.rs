//! Complete finite-lemma check under frozen protocol d52cb6.
#![allow(dead_code)]

#[cfg(test)]
mod tests {
    use chained_original_smith_engine::original;
    use serde_json::{json, Value};
    use std::collections::{BTreeMap, BTreeSet, HashSet};
    use std::fs::OpenOptions;
    use std::io::{BufWriter, Write};

    type Matrix = [u8; 6];
    fn pairing(a: u8, b: u8) -> u32 {
        let swapped = ((a & 0x15) << 1) | ((a & 0x2a) >> 1);
        (swapped & b).count_ones() & 1
    }
    fn original_pairing(a: u8, b: u8) -> u32 {
        (a & b).count_ones() & 1
    }
    fn q0(a: u8) -> u32 {
        (a & (a >> 1) & 0x15).count_ones() & 1
    }
    fn act(m: &Matrix, mut a: u8) -> u8 {
        let mut out = 0;
        while a != 0 {
            let bit = a.trailing_zeros() as usize;
            out ^= m[bit];
            a &= a - 1;
        }
        out
    }
    fn packed(m: &Matrix) -> u64 {
        m.iter()
            .enumerate()
            .fold(0, |v, (i, &c)| v | ((c as u64) << (6 * i)))
    }
    fn assert_symplectic(m: &Matrix) {
        for i in 0..6 {
            for j in 0..6 {
                assert_eq!(
                    pairing(m[i], m[j]),
                    if i / 2 == j / 2 && i != j { 1 } else { 0 }
                );
            }
        }
    }
    fn odd_coefficients() -> Vec<u8> {
        (0..64).filter(|&a| q0(a) == 1).collect()
    }
    fn pullback(m: &Matrix, beta: u8) -> u8 {
        m.iter().enumerate().fold(0, |out, (i, &column)| {
            let value = q0(column) ^ ((beta & column).count_ones() & 1);
            out | ((value as u8) << i)
        })
    }
    fn odd_permutation(m: &Matrix, odds: &[u8]) -> Vec<usize> {
        odds.iter()
            .map(|&beta| odds.binary_search(&pullback(m, beta)).unwrap())
            .collect()
    }
    fn cycle_type(permutation: &[usize]) -> Vec<usize> {
        let mut seen = vec![false; permutation.len()];
        let mut cycles = vec![];
        for i in 0..permutation.len() {
            if seen[i] {
                continue;
            }
            let mut at = i;
            let mut n = 0;
            while !seen[at] {
                seen[at] = true;
                n += 1;
                at = permutation[at];
            }
            assert_eq!(at, i, "not a permutation");
            cycles.push(n);
        }
        cycles.sort();
        cycles
    }
    fn audit_quadratic_formula(m: &Matrix) {
        for beta in 0..64u8 {
            for x in 0..64u8 {
                let y = act(m, x);
                let next = pullback(m, beta);
                assert_eq!(
                    q0(y) ^ ((beta & y).count_ones() & 1),
                    q0(x) ^ ((next & x).count_ones() & 1)
                );
            }
        }
    }
    fn stable_count(images: &[u8; 64], kernels: &[u64]) -> usize {
        kernels
            .iter()
            .filter(|&&space| {
                let mut rest = space;
                while rest != 0 {
                    let v = rest.trailing_zeros() as usize;
                    rest &= rest - 1;
                    if space & (1u64 << images[v]) == 0 {
                        return false;
                    }
                }
                true
            })
            .count()
    }
    fn original_basis() -> (Matrix, [u8; 64], [u8; 128]) {
        let mut remaining: Vec<u8> = (0..128u8)
            .filter(|v| v.count_ones().is_multiple_of(2))
            .collect();
        assert_eq!(remaining.len(), 64);
        let mut basis = [0; 6];
        for pair in 0..3 {
            let e = *remaining.iter().find(|&&v| v != 0).unwrap();
            let f = *remaining
                .iter()
                .find(|&&v| original_pairing(e, v) == 1)
                .unwrap();
            basis[2 * pair] = e;
            basis[2 * pair + 1] = f;
            remaining.retain(|&v| original_pairing(e, v) == 0 && original_pairing(f, v) == 0);
            assert_eq!(remaining.len(), 1usize << (4 - 2 * pair));
        }
        let masks: [u8; 64] = std::array::from_fn(|v| act(&basis, v as u8));
        let mut inverse = [255; 128];
        for (v, &mask) in masks.iter().enumerate() {
            assert_eq!(inverse[mask as usize], 255);
            inverse[mask as usize] = v as u8;
        }
        for a in 0..64 {
            for b in 0..64 {
                assert_eq!(
                    pairing(a as u8, b as u8),
                    original_pairing(masks[a], masks[b])
                );
            }
        }
        for a in 0..64 {
            assert_eq!(inverse[masks[a] as usize], a as u8);
        }
        (basis, masks, inverse)
    }

    fn rank(vectors: &[u8]) -> usize {
        let mut pivots = [0; 6];
        for &vector in vectors {
            let mut v = vector;
            for i in (0..6).rev() {
                if v & (1 << i) == 0 {
                    continue;
                }
                if pivots[i] == 0 {
                    pivots[i] = v;
                    break;
                }
                v ^= pivots[i];
            }
        }
        pivots.iter().filter(|&&x| x != 0).count()
    }
    fn images(m: &Matrix) -> [u8; 64] {
        std::array::from_fn(|x| act(m, x as u8))
    }

    #[test]
    fn all_symplectic_actions_compatible_with_actual_geometric_data() {
        let input: Value =
            serde_json::from_str(include_str!("../fixtures/actual-frobenius.json")).unwrap();
        let target_perm: Vec<usize> = input["native_bitangent_frobenius"]["permutation"]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| x.as_u64().unwrap() as usize)
            .collect();
        assert_eq!(target_perm.len(), 28);
        assert!(target_perm.iter().all(|&x| x < 28));
        let target_type = cycle_type(&target_perm);
        let orders: Vec<u64> = input["native_two_primary_group"]["exact_orders"]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| x.as_u64().unwrap())
            .collect();
        assert_eq!(orders.len(), 4);
        assert!(orders.iter().all(|&x| x > 0));
        let target_fixed = orders.iter().filter(|&&x| 2 % x == 0).count();
        let (basis, masks, inverse) = original_basis();
        let original_lags = original::lagrangians();
        assert_eq!(original_lags.len(), 135);
        let mut kernel_set = BTreeSet::new();
        for (space, _) in &original_lags {
            let vectors: Vec<_> = space
                .iter()
                .map(|&x| {
                    assert!(x < 128);
                    let v = inverse[x as usize];
                    assert!(v < 64);
                    v
                })
                .collect();
            assert_eq!(vectors.iter().copied().collect::<BTreeSet<_>>().len(), 7);
            assert!(vectors.iter().all(|&v| v != 0));
            assert_eq!(rank(&vectors), 3);
            for &a in &vectors {
                for &b in &vectors {
                    assert_eq!(pairing(a, b), 0);
                    assert!(a == b || vectors.contains(&(a ^ b)));
                }
            }
            let bits = vectors.iter().fold(0u64, |bits, &v| bits | (1u64 << v));
            assert!(kernel_set.insert(bits));
        }
        assert_eq!(kernel_set.len(), 135);
        let kernels: Vec<_> = kernel_set.into_iter().collect();
        let odds = odd_coefficients();
        assert_eq!(odds.len(), 28);
        let identity: [u8; 6] = std::array::from_fn(|i| 1 << i);
        assert_symplectic(&identity);
        audit_quadratic_formula(&identity);
        assert_eq!(stable_count(&images(&identity), &kernels), 135);
        assert_eq!(
            odd_permutation(&identity, &odds)
                .iter()
                .enumerate()
                .filter(|&(i, &j)| i == j)
                .count(),
            28
        );
        let mut transvection = identity;
        transvection[1] ^= 1;
        assert_symplectic(&transvection);
        audit_quadratic_formula(&transvection);
        assert_eq!(stable_count(&images(&transvection), &kernels), 15);
        let trans_perm = odd_permutation(&transvection, &odds);
        assert_eq!(
            trans_perm
                .iter()
                .enumerate()
                .filter(|&(i, &j)| i == j)
                .count(),
            16
        );
        let root_perm = original::perm_of_type(&[6, 1, 1]);
        let representative: Matrix = std::array::from_fn(|i| {
            let mask = basis[i];
            let mut next = 0u8;
            for bit in 0..8 {
                if mask & (1 << bit) != 0 {
                    next |= 1 << root_perm[bit];
                }
            }
            if next & 0x80 != 0 {
                next = !next;
            }
            inverse[next as usize]
        });
        assert_symplectic(&representative);
        audit_quadratic_formula(&representative);
        let representative_images = images(&representative);
        let original_counts = original::stable_kernels(&root_perm, &original_lags);
        let representative_stable = stable_count(&representative_images, &kernels);
        assert_eq!(representative_stable, original_counts.1 as usize);
        assert_eq!(
            cycle_type(&odd_permutation(&representative, &odds)),
            target_type
        );
        assert_eq!(
            representative_images
                .iter()
                .enumerate()
                .filter(|&(i, &v)| i == v as usize)
                .count(),
            target_fixed
        );

        let output = std::path::PathBuf::from(
            std::env::var_os("N4_KERNEL_CENSUS_OUT")
                .expect("explicit outside raw capture path required"),
        );
        assert_eq!(
            output.file_name().and_then(|n| n.to_str()),
            Some("all-symplectic-matrices.bin")
        );
        let parent = output.parent().unwrap().canonicalize().unwrap();
        let source = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .canonicalize()
            .unwrap();
        assert!(
            !parent.starts_with(source.ancestors().nth(3).unwrap()),
            "output inside consumer source"
        );
        let mut writer = BufWriter::new(
            OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&output)
                .unwrap(),
        );
        writer.write_all(b"CTSP6V1\n").unwrap();
        let mut all = HashSet::with_capacity(1_451_520);
        let mut histogram = BTreeMap::new();
        let mut examined = 0usize;
        let mut matched = 0usize;
        for e1 in 1..64u8 {
            let partners1: Vec<_> = (1..64u8).filter(|&v| pairing(e1, v) == 1).collect();
            assert_eq!(partners1.len(), 32);
            for f1 in partners1 {
                let orth1: Vec<_> = (0..64u8)
                    .filter(|&v| pairing(e1, v) == 0 && pairing(f1, v) == 0)
                    .collect();
                assert_eq!(orth1.len(), 16);
                for &e2 in orth1.iter().filter(|&&v| v != 0) {
                    let partners2: Vec<_> = orth1
                        .iter()
                        .copied()
                        .filter(|&v| pairing(e2, v) == 1)
                        .collect();
                    assert_eq!(partners2.len(), 8);
                    for f2 in partners2 {
                        let orth2: Vec<_> = orth1
                            .iter()
                            .copied()
                            .filter(|&v| pairing(e2, v) == 0 && pairing(f2, v) == 0)
                            .collect();
                        assert_eq!(orth2.len(), 4);
                        for &e3 in orth2.iter().filter(|&&v| v != 0) {
                            let partners3: Vec<_> = orth2
                                .iter()
                                .copied()
                                .filter(|&v| pairing(e3, v) == 1)
                                .collect();
                            assert_eq!(partners3.len(), 2);
                            for f3 in partners3 {
                                let matrix = [e1, f1, e2, f2, e3, f3];
                                assert_symplectic(&matrix);
                                let code = packed(&matrix);
                                assert!(all.insert(code));
                                examined += 1;
                                let image = images(&matrix);
                                let fixed = image
                                    .iter()
                                    .enumerate()
                                    .filter(|&(i, &v)| i == v as usize)
                                    .count();
                                let mut count = 255u8;
                                if fixed == target_fixed
                                    && cycle_type(&odd_permutation(&matrix, &odds)) == target_type
                                {
                                    for v in 0..64u8 {
                                        let mut w = v;
                                        for _ in 0..6 {
                                            w = act(&matrix, w);
                                        }
                                        assert_eq!(v, w);
                                    }
                                    let stable = stable_count(&image, &kernels);
                                    assert!(stable <= 135);
                                    count = stable as u8;
                                    matched += 1;
                                    *histogram.entry(stable).or_insert(0usize) += 1;
                                }
                                writer.write_all(&code.to_le_bytes()).unwrap();
                                writer.write_all(&[count]).unwrap();
                            }
                        }
                    }
                }
            }
        }
        assert_eq!(examined, 1_451_520);
        assert_eq!(all.len(), examined);
        assert!(matched > 0);
        assert_eq!(histogram.values().sum::<usize>(), matched);
        writer.flush().unwrap();
        drop(writer);
        let raw_bytes = std::fs::metadata(&output).unwrap().len();
        assert_eq!(raw_bytes, 8 + 9 * examined as u64);
        println!(
            "N4_KERNEL_CENSUS_INPUT {}",
            json!({"actual_odd_cycle_type":target_type,"actual_rational_2torsion_fixed":target_fixed,"literal_actual_permutation":target_perm,"original_rational_cofactor_orders":orders,"scope":"actualcoordinate/tableinputs;theta/Galoisbridge written,notactualJac2basis"})
        );
        println!(
            "N4_KERNEL_CENSUS_CONTROLS {}",
            json!({"original_abstract_symplectic_basis":basis,"all64_vector_roundtrips":true,"all4096_pairings":true,"all135_original_kernels_rank3_closed_isotropic_distinct":true,"identity_kernels":135,"identity_odd_fixed":28,"transvection_kernels":15,"transvection_odd_fixed":16,"S8_control_type":[6,1,1],"original_S8_pair_and_any_counts":original_counts,"generic_representative_stable_count":representative_stable,"three_controls_full_quadratic_identities":true,"abstract_model_not_actualWeierstrasspoints":true,"basis_mask_table":masks.to_vec()})
        );
        println!(
            "N4_KERNEL_CENSUS_FULL {}",
            json!({"examined_distinct_symplectic_actions":examined,"matched_both_actual_predicates":matched,"stable_kernel_count_histogram":histogram,"raw_binary_file":"all-symplectic-matrices.bin","raw_binary_bytes":raw_bytes,"raw_schema":"CTSP6V1newline(8bytes);everyframe:u64LE6columns6bits,u8count255ifnotmatched","every_examined_matrix_recorded":true,"group_order_bridge":"63*32*15*8*3*2 plus standardSp6order/cardinality;written"})
        );
        println!(
            "N4_KERNEL_CENSUS_SCOPE {}",
            json!({"scope":"completefinitealgebra census observations;standardtheta/Frobenius/symplectic/completeness/quotientbridges written;noactualtorsionbasis/kernelcoordinates/codomain/newnondualmaporcostcomparison","predicted_histogram_not_an_acceptance_condition":true})
        );
    }
}
