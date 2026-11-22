//! Independent coupled-port and nested-precision controls for the source path.

use super::*;
use crate::contraction::{Edge, Tensor, TensorKind, TensorVertex};
use crate::network::FnPredicate;
use crate::Limits;
use std::sync::Arc;

fn predicate(arity: usize, table: u8) -> Arc<Tensor> {
    Arc::new(Tensor {
        creation_precision: 3,
        kind: TensorKind::Boolean(Arc::new(FnPredicate::new(arity, move |bits, _| {
            let index = bits
                .iter()
                .enumerate()
                .fold(0, |n, (i, bit)| n | (usize::from(*bit) << i));
            Ok(table & (1 << index) != 0)
        }))),
    })
}

fn forced(
    graph: &Bipartite,
    ring: &Ring,
    rows: Vec<usize>,
    columns: Vec<usize>,
    layers: usize,
    meter: &mut Meter,
) -> Result<Element> {
    if layers == 0 || graph.edges.is_empty() {
        return brute_tensor(graph, ring, &mut Statistics::default(), meter);
    }
    let parameters = Parameters {
        radix: 2,
        u: 1,
        a: 2,
        length: 4,
        array: 16,
    };
    let packing = packing::pack_labels(graph, &parameters, rows, columns, false, meter)?;
    active(
        graph,
        ring,
        &parameters,
        &packing,
        false,
        usize::MAX,
        &mut |child, child_ring, work| {
            forced(
                child,
                child_ring,
                vec![0; child.left.len()],
                vec![3; child.right.len()],
                layers - 1,
                work,
            )
        },
        meter,
    )
}

#[test]
fn coupled_packets_match_direct_counts_with_parallel_ports_and_quadratic_modes() {
    let mut meter = Meter::new(Limits {
        steps: 5_000_000_000,
        ..Limits::default()
    });
    let ring = Ring::new(4, 3, &mut meter).unwrap();
    // Two inputs of the same predicate are correlated. Treating their mode
    // sums independently would lose that correlation.
    let parallel = Bipartite {
        left: vec![TensorVertex {
            tensor: predicate(2, 6),
            edges: vec![0, 1],
        }],
        right: vec![TensorVertex {
            tensor: predicate(2, 6),
            edges: vec![0, 1],
        }],
        edges: vec![
            Edge {
                left: (0, 0),
                right: (0, 0),
            },
            Edge {
                left: (0, 1),
                right: (0, 1),
            },
        ],
    };
    parallel.validate().unwrap();
    let expected = brute_tensor(&parallel, &ring, &mut Statistics::default(), &mut meter).unwrap();
    assert_eq!(expected, ring.integer(&2u8.into()));
    assert_eq!(
        forced(&parallel, &ring, vec![0], vec![3], 1, &mut meter).unwrap(),
        expected
    );

    // Both rows lie in the same target group and the columns occupy j=0,1
    // in one packet. Its degree-two incoming coefficient and outgoing form
    // powers must be retained, including the mixed term with coefficient 2.
    for right_tables in [[3u8, 3u8], [2, 1]] {
        let graph = Bipartite {
            left: (0..2)
                .map(|edge| TensorVertex {
                    tensor: predicate(1, 2),
                    edges: vec![edge],
                })
                .collect(),
            right: right_tables
                .iter()
                .enumerate()
                .map(|(edge, &table)| TensorVertex {
                    tensor: predicate(1, table),
                    edges: vec![edge],
                })
                .collect(),
            edges: vec![
                Edge {
                    left: (0, 0),
                    right: (0, 0),
                },
                Edge {
                    left: (1, 0),
                    right: (1, 0),
                },
            ],
        };
        graph.validate().unwrap();
        let expected = brute_tensor(&graph, &ring, &mut Statistics::default(), &mut meter).unwrap();
        let actual = forced(&graph, &ring, vec![0, 2], vec![3, 1], 1, &mut meter).unwrap();
        assert_eq!(actual, expected, "column predicates {right_tables:?}");
    }
}

#[test]
fn coupled_nested_contraction_preserves_old_packet_creation_precision() {
    let mut meter = Meter::new(Limits {
        steps: 5_000_000_000,
        ..Limits::default()
    });
    let ring = Ring::new(4, 3, &mut meter).unwrap();
    let graph = Bipartite {
        left: vec![TensorVertex {
            tensor: predicate(1, 2),
            edges: vec![0],
        }],
        right: vec![TensorVertex {
            tensor: predicate(1, 3),
            edges: vec![0],
        }],
        edges: vec![Edge {
            left: (0, 0),
            right: (0, 0),
        }],
    };
    graph.validate().unwrap();
    let expected = brute_tensor(&graph, &ring, &mut Statistics::default(), &mut meter).unwrap();
    assert_eq!(
        forced(&graph, &ring, vec![0], vec![3], 2, &mut meter).unwrap(),
        expected
    );
}

#[test]
fn both_taper_levels_match_direct_counts_for_crossing_and_local_ports() {
    let mut meter = Meter::new(Limits {
        steps: 5_000_000_000,
        ..Limits::default()
    });
    let ring = Ring::new(4, 3, &mut meter).unwrap();
    let parameters = Parameters {
        radix: 2,
        u: 2,
        a: 2,
        length: 4,
        array: 16,
    };
    // Existing forced controls retain only odd Hermite nodes (u=1).
    // Here both v2(t)=0 and v2(t)=1 contribute, selecting different label
    // coordinates and different multiplicities/child precisions.
    for (rows, columns) in [(0, 3), (1, 2), (2, 2)] {
        for (left_table, right_table) in [(6, 15), (9, 6), (15, 15)] {
            let graph = Bipartite {
                left: vec![TensorVertex {
                    tensor: predicate(2, left_table),
                    edges: vec![0, 1],
                }],
                right: vec![TensorVertex {
                    tensor: predicate(2, right_table),
                    edges: vec![0, 1],
                }],
                edges: vec![
                    Edge {
                        left: (0, 0),
                        right: (0, 0),
                    },
                    Edge {
                        left: (0, 1),
                        right: (0, 1),
                    },
                ],
            };
            let packing = packing::pack_labels(
                &graph,
                &parameters,
                vec![rows],
                vec![columns],
                false,
                &mut meter,
            )
            .unwrap();
            let expected =
                brute_tensor(&graph, &ring, &mut Statistics::default(), &mut meter).unwrap();
            let actual = active(
                &graph,
                &ring,
                &parameters,
                &packing,
                false,
                usize::MAX,
                &mut |child, child_ring, work| {
                    brute_tensor(child, child_ring, &mut Statistics::default(), work)
                },
                &mut meter,
            )
            .unwrap();
            assert_eq!(
                actual, expected,
                "labels {rows}/{columns}, tables {left_table}/{right_table}"
            );
        }
    }
}
