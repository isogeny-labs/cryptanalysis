---
name: lmfdb-local-query
description: Query local LMFDB indexes with provenance for elliptic curves over Q and number fields, genus 2 curves, and finite-field abelian-variety isogeny classes. Use when catalog data informs curve or isogeny analysis; these indexes do not cover arbitrary cryptographic challenge curves.
---

# Local LMFDB curve queries

Run `tools/lmfdb/query.py` from the repository root using a Python environment
with DuckDB. On this Mac, `/Users/adamburan/.pyenv/versions/3.9.10/bin/python3`
has DuckDB. Pass `--dataset-dir /Volumes/SSD990/llm/tmp/lmfdb-query-cache-20261025`
for repeated queries, or `--dataset-dir /Volumes/data/workspaces/lmfdb-agent-query-20261019/data`
for the NAS source. Begin with `--list`; a dataset is available only when its
manifest says `complete: true` and its Parquet file exists. If `/Volumes/data`
is unavailable, check the NAS mount before concluding the data is missing;
reconnects can appear at `/Volumes/data-1`.

Choose `ec_q` for elliptic curves over Q, `ec_nf` for elliptic curves over
number fields, `g2c` for genus 2 curves, and `av_fq` for finite-field
abelian-variety **isogeny classes**. `av_fq` rows are classes, not individual
curves. `--conductor` means conductor for `ec_q`, conductor norm for `ec_nf`,
and `cond` for `g2c`; it is unavailable for `av_fq`. Use `--schema` to inspect
the selected columns and `--metadata` to inspect extraction provenance.

```sh
python3 tools/lmfdb/query.py --dataset-dir /Volumes/SSD990/llm/tmp/lmfdb-query-cache-20261025 --label 11.a1
python3 tools/lmfdb/query.py --dataset-dir /Volumes/SSD990/llm/tmp/lmfdb-query-cache-20261025 --table av_fq --label 2.625.r_fv
python3 tools/lmfdb/query.py --dataset-dir /Volumes/SSD990/llm/tmp/lmfdb-query-cache-20261025 --sql 'SELECT lmfdb_label, conductor, rank FROM ec_q WHERE conductor < 1000 AND rank >= 2 ORDER BY conductor' --limit 100
```

Include the exact label, source table, and extraction window with any result
used in a research artifact. The four indexes contain selected fields and
were extracted separately; a cross-index join is not a transactionally
consistent snapshot. Null values remain unknown, and `rank` and
`analytic_rank` are distinct fields. If the requested family or field is
absent, say so rather than inferring it from another index.

An LMFDB label does not establish the identity or ECDLP hardness of a
cryptographic challenge curve. Verify its field, equation/model, subgroup
order, cofactor, generator, and target metadata against the challenge
registry before making a crosswalk or hardness claim.

The broader public export is at
`/Volumes/data/workspaces/lmfdb-public-mirror-20261019/resumable/`. Treat it
as a complete archive only when `COMPLETE.json` validates. The read-only LAN
endpoint and NAS share are documented at
`/Volumes/data/workspaces/lmfdb-network-20261025/README.md`; the endpoint
offers bounded lookup/filter operations over the four indexes after archive
verification. See [tool usage](../../../tools/lmfdb/README.md) for local
commands and coverage.
