# Prospective HTTP evidence transport amendment

Scientific commands, source snapshot, targets, seeds and limits remain bound
by `launch.sha256`. This amendment changes only control/evidence transport.

Read-only documented provider logs establish that pod `uf7o6868cpoxi7`
started its SSH server at 04:52:00 UTC, listening on IPv4/IPv6 port22.
Direct SSH from the execution environment remained unavailable. Provider
v2 metadata confirms a running RTX5090, 125GB host memory and28vCPU. These
are provider metadata, not a native CUDA doctor or a GPU measurement.

Root may deliver the pinned package through a repository artifact URL and
expose the Runpod HTTPS proxy for port8888. `remote_http.py` starts only the
fixed frozen launcher under a4500-second timeout and60-second kill grace.
Its two authenticated GET routes are `/status` and `/evidence.tar.gz`.
Authentication uses a new random `IDEAS_HTTP_BEARER` nonce; it is separate
from the user/provider API key and is never written into evidence. The
scientific subprocess inherits neither nonce nor `RUNPOD_API_KEY`. No
arbitrary command, file-path, browser terminal or TCP-forwarding endpoint
is supplied. Root owns all provider mutations, billing deadlines, artifact
retrieval and pod deletion.

After the launcher exits, the server atomically archives `remote/run-0`,
including all logs, resources, JSON, raw DP/checkpoint records and a per-file
SHA256 manifest. CUDA toolchain/build trees and compiled ELF executables
are excluded; their pinned source/build/binary hashes remain in the
records. Authenticated `/status` reports terminal return code, archive
readiness, byte count and SHA256. The archived adapter-state record precedes
the archive's own digest/readiness metadata; the final authenticated status
is retained separately by the root controller. The server stays available
for evidence retrieval after the workload finishes. External STOP/DELETE,
not the HTTP server's process lifetime, enforces provider billing cleanup.

This is an infrastructure change and does not turn preparation or provider
metadata into an executed scientific result. No pod was provisioned,
modified or deleted by this workstream.
