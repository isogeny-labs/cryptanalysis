//! Independent truth-table controls for finite exact planning and propagation.
use hashed_ecdl_tensor::network::{direct_count, FnPredicate, GraphBuilder};
use hashed_ecdl_tensor::{width, Error, Limits, Meter};

#[test]
fn exact_elimination_and_slicing_match_all_two_port_truth_tables_and_pins() {
    let mut meter = Meter::new(Limits::default());
    for a in 0..16u8 {
        for b in 0..16u8 {
            let mut builder = GraphBuilder::new();
            let left = builder.vertex(FnPredicate::new(2, move |x, _| {
                Ok(a & (1 << (usize::from(x[0]) + 2 * usize::from(x[1]))) != 0)
            }));
            let right = builder.vertex(FnPredicate::new(2, move |x, _| {
                Ok(b & (1 << (usize::from(x[0]) + 2 * usize::from(x[1]))) != 0)
            }));
            let x = builder.edge(left, right, &mut meter).unwrap();
            let y = builder.edge(left, right, &mut meter).unwrap();
            let graph = builder.finish(vec![x, y]).unwrap();
            for pins in [
                [None, None],
                [Some(false), None],
                [None, Some(true)],
                [Some(true), Some(false)],
            ] {
                let expected = direct_count(&graph, &pins, &mut meter).unwrap();
                for rank in [0, 1, 2] {
                    let plan = width::plan(
                        &graph,
                        &pins,
                        &width::Policy {
                            maximum_rank: rank,
                            maximum_slices: 2,
                        },
                        &mut meter,
                    )
                    .unwrap();
                    assert_eq!(
                        width::count(&graph, &pins, &plan, &mut meter).unwrap(),
                        expected
                    );
                    let witness = width::witness(&graph, &pins, &plan, &mut meter).unwrap();
                    assert_eq!(witness.is_some(), expected != 0u8.into());
                    if let Some(word) = witness {
                        assert!(graph.evaluate(&word, &mut meter).unwrap());
                        for (pin, bit) in pins.iter().zip(word) {
                            assert!(pin.map_or(true, |p| p == bit));
                        }
                    }
                }
            }
        }
    }
}

#[test]
fn plans_reject_missing_duplicate_pinned_and_understated_edges() {
    let mut meter = Meter::new(Limits::default());
    let mut builder = GraphBuilder::new();
    let a = builder.vertex(FnPredicate::new(2, |_, _| Ok(true)));
    let b = builder.vertex(FnPredicate::new(2, |_, _| Ok(true)));
    builder.edge(a, b, &mut meter).unwrap();
    builder.edge(a, b, &mut meter).unwrap();
    let graph = builder.finish(vec![]).unwrap();
    for plan in [
        width::Plan {
            slices: vec![],
            order: vec![0],
            maximum_rank: 2,
        },
        width::Plan {
            slices: vec![0],
            order: vec![0, 1],
            maximum_rank: 2,
        },
        width::Plan {
            slices: vec![],
            order: vec![0, 1],
            maximum_rank: 1,
        },
    ] {
        assert!(plan.validate(&graph, &[None, None], &mut meter).is_err());
    }
    assert!(width::Plan {
        slices: vec![],
        order: vec![0, 1],
        maximum_rank: 2
    }
    .validate(&graph, &[Some(true), None], &mut meter)
    .is_err());
    assert!(matches!(
        width::plan(
            &graph,
            &[None, None],
            &width::Policy {
                maximum_rank: 0,
                maximum_slices: 0
            },
            &mut meter
        ),
        Err(Error::Limit(_))
    ));
}

#[test]
fn witness_only_does_not_require_count_precision_or_exponential_tables() {
    let mut meter = Meter::new(Limits {
        bits: 1,
        vector: 20_000,
        steps: 100_000,
    });
    let mut builder = GraphBuilder::new();
    let a = builder.vertex(FnPredicate::new(70, |bits, _| Ok(bits.iter().all(|b| !b))));
    let b = builder.vertex(FnPredicate::new(70, |_, _| Ok(true)));
    for _ in 0..70 {
        builder.edge(a, b, &mut meter).unwrap();
    }
    let graph = builder.finish((0..70).collect()).unwrap();
    let plan = width::Plan {
        slices: (0..70).collect(),
        order: vec![],
        maximum_rank: 0,
    };
    let word = width::witness(&graph, &[None; 70], &plan, &mut meter)
        .unwrap()
        .unwrap();
    assert_eq!(word, vec![false; 70]);
    assert!(matches!(
        width::count(&graph, &[None; 70], &plan, &mut meter),
        Err(Error::Limit(_))
    ));
    meter.limits.steps = meter.used;
    assert!(matches!(
        width::witness(&graph, &[None; 70], &plan, &mut meter),
        Err(Error::Limit(_))
    ));
}

#[test]
fn isolated_false_scalar_is_unsat_with_no_free_edges() {
    let mut meter = Meter::new(Limits::default());
    let mut builder = GraphBuilder::new();
    builder.vertex(FnPredicate::new(0, |_, _| Ok(false)));
    let graph = builder.finish(vec![]).unwrap();
    let plan = width::plan(&graph, &[], &width::Policy::default(), &mut meter).unwrap();
    assert_eq!(
        width::count(&graph, &[], &plan, &mut meter).unwrap(),
        0u8.into()
    );
    assert!(width::witness(&graph, &[], &plan, &mut meter)
        .unwrap()
        .is_none());
}
