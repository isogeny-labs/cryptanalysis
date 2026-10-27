# Local LMFDB curve indexes

`query.py` reads completed Parquet indexes of selected public LMFDB columns.
The index files and their manifests live outside this repository on the NAS;
the verified SSD cache on this Mac supports faster repeated queries. The
query tool does not need the broader PostgreSQL export to be complete.

| View | Content | Scope |
| --- | --- | --- |
| `ec_q` | elliptic curves over Q | selected columns from `ec_curvedata` |
| `ec_nf` | elliptic curves over number fields | selected columns from `ec_nfcurves` |
| `g2c` | genus 2 curves | selected columns from `g2c_curves_new` |
| `av_fq` | finite-field abelian-variety isogeny classes | classes from `av_fq_isog`, not individual curves |

On this Mac, use the Python environment with DuckDB and list completed
datasets first:

```sh
cd /path/to/cryptanalysis
/Users/adamburan/.pyenv/versions/3.9.10/bin/python3 tools/lmfdb/query.py \
  --dataset-dir /Volumes/SSD990/llm/tmp/lmfdb-query-cache-20261025 --list
/Users/adamburan/.pyenv/versions/3.9.10/bin/python3 tools/lmfdb/query.py \
  --dataset-dir /Volumes/SSD990/llm/tmp/lmfdb-query-cache-20261025 \
  --label 11.a1 --limit 1
```

Use `/Volumes/data/workspaces/lmfdb-agent-query-20261019/data` as
`--dataset-dir` when the SSD cache is absent and the NAS is mounted. The CLI
supports `--schema`, `--metadata`, `--label`, `--conductor`, and one bounded
`SELECT` or `WITH` query via `--sql`. Inspect the schema before querying
fields that may not exist in every view. Results include their source table,
extraction window, and row count. Each index was extracted independently, so
cross-view joins do not represent one database transaction. Null fields mean
missing or unknown data.

The [agent skill](../../.agents/skills/lmfdb-local-query/SKILL.md) gives
query and identity guidance. The broader archive is at
`/Volumes/data/workspaces/lmfdb-public-mirror-20261019/resumable/`; its
`COMPLETE.json` marker is the completion gate. The LAN endpoint and NAS share
are documented in `/Volumes/data/workspaces/lmfdb-network-20261025/README.md`.
