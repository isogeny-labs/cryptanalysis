# Post-run output archive amendment

The frozen solver runs and their summaries preceded this amendment. `msolve`
writes parametrizations with trailing spaces. To keep the exact output bytes
while satisfying the repository diff check, `archive_outputs.py` checks each
uncompressed output's SHA-256 against the frozen run summary, `[pcc:unverified]`
then stores it as deterministic gzip (`mtime=0`) and removes the plain text
copy. Inputs, solver logs, result summaries, and measurements are unchanged.
The validators decompress the stored outputs and check the original hashes.
This changes only artifact encoding and is not a new solver run.
