use chained_transfer_lp_finite_projection_01::projection;
use chained_transfer_lp_historical_01::{
    assembly::{assemble, Column},
    public_view,
    types::{Available, Graph, PublicCall},
};
use serde_json::json;

fn available(vertices: usize) -> Available {
    Available {
        factor_base: vec![[1, 0, 0], [1, 1, 0], [1, 2, 0]],
        full_rows: vec![],
        combined_lp_cycle_rows: vec![],
        graph: Graph {
            full: vec![],
            ground: vec![],
            edges: vec![],
            vertex_points: (0..vertices).map(|i| [1, 80 + i as u64, 0]).collect(),
            pairs: 0,
            no_roots: 0,
        },
        columns: 3,
        eta_column: 2,
    }
}

#[test]
fn complete_raw_fixture_family_and_independent_projection_replay() {
    let mut cases = Vec::new();
    let mut a = available(4);
    a.graph.edges = vec![(0, 1, 0, 1), (1, 2, 0, 2), (2, 3, 0, 1), (3, 0, 1, 1)];
    cases.push(("ungrounded_even_four_cycle", a, 2, 3));
    let mut a = available(3);
    a.graph.edges = vec![(0, 1, 0, 1), (1, 2, 0, 1), (2, 0, 0, 1)];
    cases.push(("lone_odd_triangle", a, 3, 3));
    let mut a = available(5);
    a.graph.edges = vec![
        (0, 1, 0, 1),
        (1, 2, 0, 1),
        (2, 0, 0, 1),
        (0, 3, 0, 2),
        (3, 4, 0, 2),
        (4, 0, 0, 2),
    ];
    cases.push(("two_odd_triangles_shared_root", a, 2, 3));
    let mut a = available(6);
    a.graph.edges = vec![
        (0, 1, 0, 1),
        (1, 2, 0, 1),
        (2, 0, 0, 1),
        (3, 4, 0, 2),
        (4, 5, 0, 2),
        (5, 3, 0, 2),
    ];
    cases.push(("two_odd_triangles_disconnected", a, 3, 3));
    let mut a = available(3);
    a.graph.edges = vec![(0, 1, 0, 1), (1, 2, 0, 1), (2, 0, 0, 1)];
    a.graph.ground = vec![(0, vec![(0, 3)], false)];
    cases.push(("grounded_odd_triangle", a, 2, 2));
    let mut a = available(2);
    a.graph.edges = vec![(0, 1, 1, 2)];
    a.graph.ground = vec![(0, vec![(1, 2)], true)];
    cases.push(("half_ground_edge", a, 3, 3));
    let mut a = available(2);
    a.graph.edges = vec![(0, 1, 0, 1)];
    a.graph.ground = vec![(0, vec![(0, 3)], false), (1, vec![(0, 3)], false)];
    cases.push(("two_grounded_endpoints", a, 2, 2));
    let mut a = available(1);
    a.graph.edges = vec![(0, 0, 0, 1)];
    cases.push(("repeated_vertex_occurrences", a, 3, 3));
    let mut a = available(0);
    a.graph.full = vec![vec![(0, 2), (1, 2)]; 2];
    a.full_rows = vec![vec![(0, 2), (2, 100)]; 2];
    cases.push(("duplicate_full_relations", a, 2, 2));
    cases.push(("isolated_large_prime", available(1), 3, 3));
    cases.push(("empty_graph", available(0), 3, 3));
    let mut a = available(0);
    a.graph.full = vec![vec![(0, 4)]];
    a.full_rows = vec![vec![(2, 100)]];
    cases.push(("all_basepoint_full_relation", a, 2, 2));
    let mut a = available(2);
    a.graph.edges = vec![(0, 1, 0, 1), (0, 1, 0, 2)];
    cases.push(("parallel_edges", a, 2, 3));
    let mut a = available(1);
    a.graph.ground = vec![(0, vec![(0, 3)], false); 2];
    cases.push(("duplicate_ground_relations", a, 3, 3));
    assert_eq!(cases.len(), 14);
    let destination =
        std::env::var_os("LP_HISTORICAL_DEVELOPMENT_OUT").map(std::path::PathBuf::from);
    if let Some(path) = &destination {
        std::fs::create_dir(path).unwrap();
    }
    let mut observations = Vec::new();
    for (name, available, expected_image, expected_uncapped) in cases {
        let p = assemble(&available, 101).unwrap();
        assert_eq!(
            p.row_map.len(),
            available.graph.full.len() + available.graph.ground.len() + available.graph.edges.len()
        );
        assert_eq!(p.columns.len(), p.a.ncols);
        assert!(matches!(p.columns.last(), Some(Column::Eta)));
        assert!(p.uncapped.rows.starts_with(&p.baseline.rows));
        let cert = projection::produce(101, &p.a, p.lp_columns, &p.baseline, &p.uncapped).unwrap();
        projection::verify(101, &p.a, p.lp_columns, &p.baseline, &p.uncapped, &cert).unwrap();
        assert_eq!(cert.p.pivots.len(), expected_image, "{name}");
        assert_eq!(
            p.uncapped.ncols - cert.u.pivots.len(),
            expected_uncapped,
            "{name}"
        );
        if name == "isolated_large_prime" {
            assert_eq!(cert.a.kernel.len(), 4);
            assert_eq!(cert.p.input.rows.len(), 4);
            assert!(cert.p.input.rows.iter().any(|v| v.iter().all(|&x| x == 0)));
        }
        if name == "repeated_vertex_occurrences" {
            assert_eq!(p.a.rows[0][0], 2);
            assert_eq!(
                p.row_map[0]
                    .terms
                    .iter()
                    .filter(|t| t.column == Some(0))
                    .count(),
                2
            );
        }
        if name == "half_ground_edge" {
            assert_eq!(p.a.rows[0][0], 2);
            assert!(p.original_rooted_receipt.lmul > 0 && p.original_rooted_receipt.ladd > 0);
        }
        let observation = json!({"name":name,"prime":101,"image_dimension":cert.p.pivots.len(),"uncapped_kernel_dimension":p.uncapped.ncols-cert.u.pivots.len(),"scope":"synthetic raw graph unit development, not the historical population"});
        if let Some(path) = &destination {
            let file = std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(path.join(format!("{name}.json")))
                .unwrap();
            serde_json::to_writer(file,&json!({"observation":observation,"entire_public_available":available,"entire_presentation":p,"entire_certificate":cert})).unwrap();
        }
        observations.push(observation);
    }
    if let Some(path) = &destination {
        serde_json::to_writer(
            std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(path.join("all14-observations.json"))
                .unwrap(),
            &observations,
        )
        .unwrap();
    }
}

#[test]
fn complete_graph_shape_and_source_occurrences_are_required() {
    let mut a = available(1);
    a.graph.ground = vec![(0, vec![(1, 2)], false)];
    assert!(assemble(&a, 101).is_err());
    a.graph.ground = vec![(1, vec![(1, 3)], false)];
    assert!(assemble(&a, 101).is_err());
    let mut a = available(0);
    a.graph.full = vec![vec![(0, 4)]];
    assert!(assemble(&a, 101).is_err()); // The entire captured full row is absent.
    a.full_rows = vec![vec![(2, 100)]];
    assert!(assemble(&a, 101).is_ok());
    a.factor_base[1] = a.factor_base[0];
    assert!(assemble(&a, 101).is_err());
}

#[test]
fn strict_public_types_reject_oracle_fields_at_every_level() {
    let call = PublicCall {
        identity: [0, 0, 0],
        ell: 101,
        available: available(0),
    };
    let original = serde_json::to_value(call).unwrap();
    for path in [vec![], vec!["available"], vec!["available", "graph"]] {
        let mut changed = original.clone();
        let mut location = &mut changed;
        for key in path {
            location = &mut location[key];
        }
        location
            .as_object_mut()
            .unwrap()
            .insert("known_logs".into(), json!([17]));
        assert!(serde_json::from_value::<PublicCall>(changed).is_err());
    }
}

fn synthetic_fixed_call(identity: [usize; 3]) -> PublicCall {
    let mut a = available(0);
    a.columns = [30, 36, 48, 64][identity[2]];
    a.eta_column = (a.columns - 1) as u32;
    a.factor_base = (0..a.columns).map(|i| [1, i as u64, 0]).collect();
    PublicCall {
        identity,
        ell: 2_773_073,
        available: a,
    }
}

#[test]
fn strict_62_record_encoding_and_header_is_not_source_verification() {
    // Empty synthetic graphs test the parser, with no historical relation or
    // Gaussian computation. The false header is refused by bind_original.
    let mut calls = Vec::new();
    for side in 0..3 {
        for target in 0..5 {
            for attempt in 0..4 {
                calls.push(synthetic_fixed_call([side, target, attempt]));
            }
        }
    }
    let view = public_view::PublicView {
        source: public_view::SourceBinding {
            bytes: 17,
            sha256: "synthetic-only".into(),
        },
        calls,
    };
    let encoded = public_view::encode(&view).unwrap();
    assert_eq!(public_view::parse(&encoded).unwrap(), view);
    assert!(public_view::bind_original(b"false original", &encoded).is_err());
    let mut lines: Vec<serde_json::Value> = encoded
        .split(|&b| b == b'\n')
        .filter(|b| !b.is_empty())
        .map(|b| serde_json::from_slice(b).unwrap())
        .collect();
    lines[1]["call"]["known_logs"] = json!([1, 2, 3]);
    let mut changed = Vec::new();
    for line in lines {
        serde_json::to_writer(&mut changed, &line).unwrap();
        changed.push(b'\n');
    }
    assert!(public_view::parse(&changed).is_err());
    assert!(public_view::parse(&encoded[..encoded.len() - 1]).is_err());
}

#[test]
fn private_field_projection_is_invariant_in_a_single_synthetic_call() {
    let call = synthetic_fixed_call([0, 0, 0]);
    let mut raw = serde_json::to_value(&call).unwrap();
    raw["known_logs"] = json!({"entire_known_point_log_table":[[42,17]]});
    raw["candidate"] = json!({"actual_vector":[1,2,3]});
    let expected = public_view::project_call(&raw).unwrap();
    raw["known_logs"] = serde_json::Value::Null;
    raw["candidate"] = json!("LP_PRIVATE_FIELD_CANARY");
    assert_eq!(public_view::project_call(&raw).unwrap(), expected);
    assert!(public_view::extract_feedback_control(b"false original", b"false control").is_err());
}
