# Data files live in the artifact store

Run outputs, relation tables, raw logs and compressed archives are kept in S3,
not in Git. The tip tree of this repository was dominated by them (about 4.0 GB
of 4.7 GB of tracked blobs), which made `actions/checkout` fail with "unable to
write file". The store moves bytes and checks them; it makes no claim about what
the bytes mean, and the evidence rules in `AGENTS.md` apply unchanged.

## What lives where

| In Git | In the store |
| --- | --- |
| Source, build files, workflows, Markdown, Lean, small reports and fixtures | Data files over the policy thresholds below |
| `.artifacts.json` in each directory: name, SHA-256, size per moved file | The bytes, at `s3://setec-astronomy-artifacts/store/sha256/ab/<hex>` |
| `.artifacts/config.json`: remote, policy, `keep` list | Write-once, content-addressed, shared with `crypto store` and the other research repositories |
| A managed block in the directory's `.gitignore` | A local cache at `~/.cache/crypto-store` (override with `ARTIFACTS_CACHE`) |

History is not rewritten. Old commits still carry old blobs; CI clones with
`filter: blob:none`, so they cost nothing there.

## Quick start

```bash
python3 tools/artifacts/artifacts.py status                 # remote, cache, entries, hydrated count
python3 tools/artifacts/artifacts.py pull experiments/foo   # before you read data under a path
python3 tools/artifacts/artifacts.py push experiments/foo/results   # instead of `git add` for data
python3 tools/artifacts/artifacts.py verify [PATH] [--remote]       # hash local files against manifests
python3 tools/artifacts/artifacts.py ls [PATH]
python3 tools/artifacts/artifacts.py plan [PATH]            # what the policy would move
```

- `pull` before you read: a checkout holds the manifests, not the bytes. Every
  download is hashed against the manifest before it is placed.
- `push` instead of `git add` for data. It uploads, writes or updates
  `.artifacts.json` and the `.gitignore` block, and removes the file from the
  index. Commit those two files with your change.
- Policy (`tools/artifacts/artifacts.py`, `DEFAULT_POLICY`): a non-code file
  over 1 MiB, or a data-suffixed file (`.jsonl .gz .json.xz .npy .bin .csv .log
  .png ...`, and `.part-NNNN` splits) over 64 KiB, belongs in the store.
  Source and text suffixes (`.rs .py .md .lean .yml .tex ...`) never move.
  PDFs stay in Git at any size.
- `keep` in `.artifacts/config.json` lists tracked files that stay in Git
  although the policy would move them: data files that code or CI outside the
  data trees names by path. Add a
  path only with the reader that needs it in the same change.
- The `artifacts` workflow runs `artifacts.py check` on every pull request and
  fails one that adds a file the policy assigns to the store. The
  `large-file-ok` label overrides it with a warning.

Credentials are the AWS CLI's (`aws sts get-caller-identity` must succeed with
access to the bucket). A `file://` remote or a read-only `https://` `read_url`
also work; see the tool docstring.

## CI

A workflow that reads moved data pulls it after checkout. `wire_workflows.py`
inserts the step; `--check` fails the `artifacts` workflow if a workflow names
moved data without it.

```yaml
- name: Pull store data this workflow reads (tools/artifacts)
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.ARTIFACTS_AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.ARTIFACTS_AWS_SECRET_ACCESS_KEY }}
    AWS_REGION: ${{ vars.ARTIFACTS_AWS_REGION || 'us-west-2' }}
  run: python3 tools/artifacts/artifacts.py pull experiments/foo
```

Repository secrets `ARTIFACTS_AWS_ACCESS_KEY_ID` and
`ARTIFACTS_AWS_SECRET_ACCESS_KEY` must be set; variable `ARTIFACTS_AWS_REGION`
is optional (default `us-west-2`). The IAM principal needs `s3:GetObject`, `s3:PutObject` and `s3:ListBucket`
on `setec-astronomy-artifacts/store/*` (and the bucket for `ListBucket`). Read
access is enough for jobs that only pull. A sparse checkout must include
`/tools/artifacts/` and the paths it pulls into.

## Rules

- `tools/artifacts/` is a shared tool, byte-identical in `crypto`,
  `cryptanalysis` and `crypto-autoresearcher`. Change it in one place and copy.
- The store is write-once. Never delete remote objects from an agent session;
  a wrong object is superseded by a new manifest entry, and removal is a human
  decision.
- Do not hand-edit `.artifacts.json` or the managed `.gitignore` block.

## Migration of existing data

One pull request, in this order:

1. `artifacts.py plan` on a full checkout (current numbers: 1,372 files,
   4,032.9 MB of 4,682.5 MB tracked would move; about 650 MB stays).
2. `artifacts.py push` by directory (`experiments/<name>`, `ecc2k130/...`),
   then `artifacts.py verify --remote`.
3. `wire_workflows.py` (without `--check`) to add the pull steps.
4. Commit the manifests, `.gitignore` blocks and workflow edits together, so no
   commit has pointers without the step that resolves them.

The `artifacts` workflow keeps the tree from growing back afterwards.
