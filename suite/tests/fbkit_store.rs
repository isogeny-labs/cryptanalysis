//! Store and S3 round trip for `ca-ic fbkit`, against the `fake_aws.sh` stub.

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};

use cryptanalysis_suite::cryptanalysis::fbkit::identity::{
    binary_curve_record, binary_field_record, curve_id, sweep_id,
};
use cryptanalysis_suite::cryptanalysis::fbkit::store::{
    download, export_archive_document, upload, AwsCli, DownloadOptions, S3Target, Store,
    UploadOptions,
};
use cryptanalysis_suite::cryptanalysis::fbkit::{CellRecord, CELL_SCHEMA, MANIFEST_SCHEMA};
use serde_json::{json, Value};

static COUNTER: AtomicUsize = AtomicUsize::new(0);

fn scratch(tag: &str) -> PathBuf {
    let p = std::env::temp_dir().join(format!(
        "fbkit-store-{}-{}-{tag}",
        std::process::id(),
        COUNTER.fetch_add(1, Ordering::SeqCst)
    ));
    let _ = fs::remove_dir_all(&p);
    p
}

fn stub(root: &Path) -> AwsCli {
    let bin = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/fake_aws.sh");
    AwsCli::new(bin).with_env("FAKE_AWS_ROOT", &root.to_string_lossy())
}

fn cell(i: u32) -> CellRecord {
    CellRecord {
        schema: CELL_SCHEMA.into(),
        cell_id: format!("coordinate-l{}-m{}-l{}-0000000{i}", i + 2, 2, i + 2),
        curve_id: "EC1N7Ckb1he2dcb29cee1f".into(),
        family: "coordinate".into(),
        recipe: json!({"family": "coordinate", "l": i + 2, "seed": 1}),
        m: 2,
        status: "complete".into(),
        reason: None,
        metrics: json!({"construction": {"fb_points": 10 + i, "geometric_points": 12,
            "usable_points": 10 + i, "effective_columns": 4, "dimension": i + 2,
            "quotient_rule": "sign", "build_ms": 0.25}}),
        ps1_label: None,
        point_set_sha256: None,
        factor_base_sha256: None,
        elapsed_seconds: 0.5,
    }
}

/// Build a populated run directory with `manifest.json`, `curve.json`, three
/// cells and one point list.
fn populate(dir: &Path) -> (Store, String, String) {
    let store = Store::create(dir).unwrap();
    let f = binary_field_record(7, &[7, 1, 0]);
    let c = binary_curve_record(1, 5, 134, -5, 67, 2, (3, 91));
    let cid = curve_id(&f, &c, "kb1").unwrap();
    store
        .write_curve(&json!({"field": f, "curve": c, "curve_id": cid}))
        .unwrap();
    let mut manifest = json!({"schema": MANIFEST_SCHEMA, "families": ["coordinate"], "jobs": 4});
    let sid = sweep_id(&manifest).unwrap();
    manifest["sweep_id"] = json!(sid);
    store.write_manifest(&manifest).unwrap();
    for i in 0..3 {
        store.write_cell(&cell(i)).unwrap();
    }
    store
        .write_points(
            &cell(0).cell_id,
            &[("2".into(), "A".into()), ("1".into(), "f".into())],
        )
        .unwrap();
    store.write_ranking(&json!({"top": []})).unwrap();
    store
        .write_report(&json!({"status": "complete"}), "# report\n")
        .unwrap();
    (store, cid, sid)
}

fn setup(tag: &str) -> (PathBuf, PathBuf, Store, S3Target, AwsCli, String) {
    let base = scratch(tag);
    let bucket = base.join("bucket");
    fs::create_dir_all(&bucket).unwrap();
    let (store, _, _) = populate(&base.join("run"));
    let target = S3Target::parse("s3://testbucket/pre/fix").unwrap();
    let aws = stub(&bucket);
    let curve = store.read_curve().unwrap();
    let prefix = target.object_prefix(
        curve["curve_id"].as_str().unwrap(),
        store.read_manifest().unwrap()["sweep_id"].as_str().unwrap(),
    );
    (base, bucket, store, target, aws, prefix)
}

fn remote_path(bucket: &Path, prefix: &str, rel: &str) -> PathBuf {
    let key = prefix.strip_prefix("s3://").unwrap();
    bucket.join(key).join(rel)
}

#[test]
fn round_trip_upload_download() {
    let (base, bucket, store, target, aws, prefix) = setup("rt");
    assert!(prefix.starts_with("s3://testbucket/pre/fix/fbkit/EC1N7Ckb1h"));
    let rep = upload(&store, Some(&target), &aws, UploadOptions::default()).unwrap();
    assert_eq!(rep.status, "complete");
    assert_eq!(rep.destination.as_deref(), Some(prefix.as_str()));
    // manifest.json is the last object.
    assert_eq!(rep.objects.last().unwrap().path, "manifest.json");
    assert_eq!(rep.objects[rep.objects.len() - 2].path, "inventory.json");
    assert_eq!(rep.count("uploaded"), rep.objects.len());
    assert!(rep.receipt.as_ref().unwrap().exists());
    assert!(remote_path(&bucket, &prefix, "cells").is_dir());

    let dir2 = base.join("copy");
    let d = download(&prefix, &dir2, &aws, DownloadOptions::default()).unwrap();
    assert_eq!(d.status, "complete");
    assert_eq!(d.verified, d.files);
    assert!(d.extra_remote.is_empty(), "{:?}", d.extra_remote);
    let copy = Store::open(&dir2).unwrap();
    assert_eq!(copy.inventory().unwrap(), store.inventory().unwrap());
    assert_eq!(
        fs::read(dir2.join("inventory.json")).unwrap(),
        fs::read(store.root().join("inventory.json")).unwrap()
    );
    assert_eq!(copy.read_cells().unwrap(), store.read_cells().unwrap());
    assert_eq!(copy.read_points(&cell(0).cell_id).unwrap()[0].0, "1");
    // A non-empty target directory is refused.
    assert!(download(&prefix, &dir2, &aws, DownloadOptions::default()).is_err());
    // Verify-only passes on the good copy (no network: a bogus binary is fine).
    let nowhere = AwsCli::new("/nonexistent/aws");
    let v = download(
        &prefix,
        &dir2,
        &nowhere,
        DownloadOptions { verify_only: true },
    )
    .unwrap();
    assert_eq!(v.status, "verified");
    let _ = fs::remove_dir_all(base);
}

#[test]
fn dry_run_uploads_nothing() {
    let (base, bucket, store, target, aws, _) = setup("dry");
    let log = base.join("aws.log");
    let aws = aws.with_env("FAKE_AWS_LOG", &log.to_string_lossy());
    let opts = UploadOptions {
        dry_run: true,
        require: false,
    };
    let rep = upload(&store, Some(&target), &aws, opts).unwrap();
    assert_eq!(rep.status, "dry_run");
    assert_eq!(rep.count("would_upload"), rep.objects.len());
    assert!(rep.total_bytes > 0);
    assert!(!log.exists(), "dry run must not invoke aws");
    assert_eq!(fs::read_dir(&bucket).unwrap().count(), 0);
    let _ = fs::remove_dir_all(base);
}

#[test]
fn unset_target_skips_or_errors() {
    let (base, _, store, _, aws, _) = setup("unset");
    let rep = upload(&store, None, &aws, UploadOptions::default()).unwrap();
    assert_eq!(rep.status, "skipped");
    let req = UploadOptions {
        dry_run: false,
        require: true,
    };
    assert!(upload(&store, None, &aws, req).is_err());
    // Missing credentials behave the same way.
    let target = S3Target::parse("s3://testbucket/p").unwrap();
    let nocred = aws.clone().with_env("FAKE_AWS_NO_CREDENTIALS", "1");
    let rep = upload(&store, Some(&target), &nocred, UploadOptions::default()).unwrap();
    assert_eq!(rep.status, "skipped");
    assert!(upload(&store, Some(&target), &nocred, req).is_err());
    let _ = fs::remove_dir_all(base);
}

#[test]
fn tampered_object_fails_download() {
    let (base, bucket, store, target, aws, prefix) = setup("tamper");
    upload(&store, Some(&target), &aws, UploadOptions::default()).unwrap();
    let victim = cell(1).cell_id;
    let rel = format!("cells/{victim}.json");
    let path = remote_path(&bucket, &prefix, &rel);
    let mut data = fs::read(&path).unwrap();
    data[10] ^= 1;
    fs::write(&path, data).unwrap();
    let dir2 = base.join("copy");
    let err = download(&prefix, &dir2, &aws, DownloadOptions::default()).unwrap_err();
    assert!(err.contains(&rel), "{err}");
    // Partial directory and a receipt remain.
    assert!(dir2.join("inventory.json").exists());
    assert!(fs::read_dir(dir2.join("receipts")).unwrap().count() == 1);
    let _ = fs::remove_dir_all(base);
}

#[test]
fn verify_only_detects_tampering() {
    let (base, _, store, _, aws, _) = setup("verify");
    store.write_inventory().unwrap();
    let nowhere = AwsCli::new("/nonexistent/aws");
    let opts = DownloadOptions { verify_only: true };
    let ok = download("", store.root(), &nowhere, opts).unwrap();
    assert_eq!(ok.status, "verified");
    let victim = store.root().join("report.md");
    fs::write(&victim, "# tampered\n").unwrap();
    let err = download("", store.root(), &aws, opts).unwrap_err();
    assert!(err.contains("report.md"), "{err}");
    // An unlisted extra file is also a failure.
    fs::write(&victim, "# report\n").unwrap();
    fs::write(store.root().join("stray.txt"), "x").unwrap();
    let err = download("", store.root(), &aws, opts).unwrap_err();
    assert!(err.contains("stray.txt"), "{err}");
    let _ = fs::remove_dir_all(base);
}

#[test]
fn second_upload_skips_unchanged_and_follows_pagination() {
    let (base, _, store, target, aws, prefix) = setup("again");
    let log = base.join("aws.log");
    let aws = aws
        .with_env("FAKE_AWS_LOG", &log.to_string_lossy())
        .with_env("FAKE_AWS_PAGE_SIZE", "2");
    let first = upload(&store, Some(&target), &aws, UploadOptions::default()).unwrap();
    assert_eq!(first.count("uploaded"), first.objects.len());
    let second = upload(&store, Some(&target), &aws, UploadOptions::default()).unwrap();
    assert_eq!(second.count("skipped"), second.objects.len());
    assert_eq!(second.uploaded_bytes, 0);
    // Change one cell: only that object (and the inventory) re-upload.
    let mut c = cell(2);
    c.elapsed_seconds = 9.0;
    store.write_cell(&c).unwrap();
    let third = upload(&store, Some(&target), &aws, UploadOptions::default()).unwrap();
    let up: Vec<&str> = third
        .objects
        .iter()
        .filter(|o| o.outcome == "uploaded")
        .map(|o| o.path.as_str())
        .collect();
    assert_eq!(up.len(), 2, "{up:?}");
    assert!(up.contains(&"inventory.json"));
    // Listing with page size 2 still sees every object.
    let keys = aws.ls(&format!("{prefix}/")).unwrap();
    assert_eq!(keys.len(), first.objects.len());
    let _ = fs::remove_dir_all(base);
}

#[test]
fn create_refuses_non_empty_and_archive_export_shape() {
    let (base, _, store, _, _, _) = setup("misc");
    assert!(Store::create(store.root()).is_err());
    assert_eq!(
        store.cell_status(&cell(0).cell_id).as_deref(),
        Some("complete")
    );
    assert_eq!(store.cell_status("nope"), None);
    let pts: Vec<(String, String)> = store.read_points(&cell(0).cell_id).unwrap();
    let mut c = cell(0);
    c.point_set_sha256 =
        Some(cryptanalysis_suite::cryptanalysis::fbkit::identity::point_set_sha256(&pts));
    let curve: Value = store.read_curve().unwrap();
    let doc = export_archive_document(&c, &curve, &pts, "fbkit test").unwrap();
    assert_eq!(doc["schema"], "ic-factor-base-archive/1");
    assert_eq!(doc["recipe"]["n"], 7);
    assert_eq!(doc["factor_base"]["actual_usable_point_count"], 10);
    assert_eq!(
        doc["factor_base"]["strict_subgroup_point_count"],
        Value::Null
    );
    assert_eq!(doc["points"][0], json!(["1", "f"]));
    let row = cryptanalysis_suite::cryptanalysis::fbkit::store::archive_index_row(
        &doc, "x.json", 5, "ab",
    );
    assert_eq!(row.len(), 18);
    assert_eq!(row[11], "True");
    let _ = fs::remove_dir_all(base);
}
