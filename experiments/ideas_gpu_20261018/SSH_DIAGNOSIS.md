# SSH startup diagnosis, 2026-10-18

Scope: read-only diagnosis and an unexecuted patch proposal. No API mutations,
pod allocation/deletion or changes to `cloud/` were made by this workstream.

The v2/v3 retained logs show their pods were created and deleted after the
300-second SSH readiness deadline. They do not contain container startup
logs or the SSH probe's captured stderr. Therefore the actual container-side
cause is **unconfirmed**; connection refusal does not by itself establish a
key or authentication problem.

`cloud/runpod_pod.py` replaces ENTRYPOINT/CMD with `bash -c STAGE0`; STAGE0
ends with `[ -x /start.sh ] && exec /start.sh`, then `exec sleep infinity`.
An absent/non-executable image script silently leaves a live pod with no
SSH. An early image-script failure exits before SSH is started. The helper
discards each readiness probe's stdout/stderr, hiding the distinction.

Upstream `runpod/containers`, main commit
`cade248dbd54da8e50bdee3ac208d5d4f98565ab`, has a startup script using
`set -e`, starting nginx before SSH and explicitly generating a legacy DSA
key before `service ssh start`. Either preceding failure can prevent SSH.
This is source evidence about upstream main, not proof of the exact bytes
inside the failed image.

- Source: https://github.com/runpod/containers/blob/cade248dbd54da8e50bdee3ac208d5d4f98565ab/container-template/start.sh
- SHA256 of downloaded current startup source:
  `2a745b3f8456da49adf23fecf72ef8dc92920d59b8c55c6d50d4788d49c24a5a`.
- Docker Hub's public tag metadata reports
  `runpod/base:1.0.2-ubuntu2404` active, amd64 compressed size 784,196,642
  bytes, image digest
  `sha256:e93bf61149910d35407fc865078ceb9b2887e986befd2b7c0eee322abe47ac59`.
  A missing tag is ruled out; successful image pull/start on the failed
  provider host remains unverified. Five minutes can also censor cold pull.

## Minimal proposal

Use the same explicit `['bash','-c']` entrypoint and preserve the lifetime
cap/prefetch prefix, but replace the image-start tail with the contents of
`ssh_start_proposal.sh`. The replacement installs only the supplied public
keys into the root authorized-keys file, generates modern host keys with
`ssh-keygen -A`, validates a dedicated public-key-only SSH configuration,
then runs `sshd -D -e` as PID1. It does not start nginx/Jupyter or export the
process environment to disk. Root must retain the externally enforced
two-hour lifecycle and eventual DELETE; SSH startup is not a billing cap.

The proposal has only been checked with `bash -n`; actual pod compatibility
still requires a successful SSH connection and native device doctor. Do not
modify the scientific launch or claim GPU execution based on this proposal.
For the next attempt, retain sanitized startup/probe failures and distinguish
image-pull/startup state from API `desiredStatus=RUNNING`.
