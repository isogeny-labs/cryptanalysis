use hashed_ecdl_tensor::curve::Point;
use hashed_ecdl_tensor::reduction::{Certificate, HashSeed};

const CERTIFICATE: &str = r#"{"version":1,"prime":[11],"threshold":[5],"seeds":[{"alpha":[1],"beta":[]}],"relations":[{"u":[1],"v":[2],"points":[{"Affine":{"x":[],"y":[1]}}]}],"dependency":[[1]],"scalar":[4]}"#;

#[test]
fn strict_json_rejects_duplicate_certificate_fields_and_nested_records() {
    let certificate: Certificate = serde_json::from_str(CERTIFICATE).unwrap();
    let value: serde_json::Value = serde_json::from_str(CERTIFICATE).unwrap();
    for (field, content) in value.as_object().unwrap() {
        let duplicated = format!("{{\"{field}\":{content},{}", &CERTIFICATE[1..]);
        let error = serde_json::from_str::<Certificate>(&duplicated)
            .unwrap_err()
            .to_string();
        assert!(error.contains("duplicate field"), "{field}: {error}");
    }
    for (original, duplicate) in [
        (r#""alpha":[1]"#, r#""alpha":[1],"\u0061lpha":[2]"#),
        (r#""beta":[]"#, r#""beta":[],"beta":[]"#),
        (r#""u":[1]"#, r#""u":[1],"u":[2]"#),
        (r#""v":[2]"#, r#""v":[2],"v":[2]"#),
        (r#""points":["#, r#""points":[],"points":["#),
        (r#""x":[]"#, r#""x":[],"x":[1]"#),
        (r#""y":[1]"#, r#""y":[1],"y":[2]"#),
    ] {
        let duplicated = CERTIFICATE.replace(original, duplicate);
        let error = serde_json::from_str::<Certificate>(&duplicated)
            .unwrap_err()
            .to_string();
        assert!(error.contains("duplicate field"), "{duplicate}: {error}");
    }
    let encoded = serde_json::to_string(&certificate).unwrap();
    assert_eq!(
        serde_json::from_str::<Certificate>(&encoded).unwrap(),
        certificate
    );
}

#[test]
fn strict_json_point_forms_reject_duplicate_variants_and_coordinates() {
    for point in [
        Point::Infinity,
        Point::Affine {
            x: 0u8.into(),
            y: 1u8.into(),
        },
    ] {
        let encoded = serde_json::to_string(&point).unwrap();
        assert_eq!(serde_json::from_str::<Point>(&encoded).unwrap(), point);
    }
    for invalid in [
        r#"{"Affine":{"x":[],"y":[1]},"Affine":{"x":[1],"y":[2]}}"#,
        r#"{"Affine":{"x":[],"x":[1],"y":[1]}}"#,
        r#"{"Affine":{"x":[],"y":[],"\u0079":[1]}}"#,
        r#"{"Affine":{"x":[],"y":[],"extra":[]}}"#,
        r#"{"Affine":{"x":[]}}"#,
        r#"{"Affine":{"y":[]}}"#,
        r#"{"Affine":{"x":[],"y":[]},"extra":null}"#,
        r#"{"Infinity":null}"#,
        r#""infinity""#,
        "null",
        "[]",
        "{}",
    ] {
        assert!(serde_json::from_str::<Point>(invalid).is_err(), "{invalid}");
    }
}

#[test]
fn strict_json_records_keep_required_fields_and_reject_unknown_fields() {
    assert!(serde_json::from_str::<HashSeed>(r#"{"alpha":[1]}"#).is_err());
    assert!(serde_json::from_str::<HashSeed>(r#"{"alpha":[1],"beta":[],"unknown":null}"#).is_err());
    let value: serde_json::Value = serde_json::from_str(CERTIFICATE).unwrap();
    for field in value.as_object().unwrap().keys() {
        let mut missing = value.clone();
        missing.as_object_mut().unwrap().remove(field);
        assert!(serde_json::from_value::<Certificate>(missing).is_err());
    }
}
