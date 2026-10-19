# shellcheck shell=bash disable=SC2034
# Trusted Bash configuration. Copy outside a repository and chmod 600.
# Values supplied on the command line override this file. Keep secrets in files
# or your provider's secret manager. This file is never downloaded implicitly.
WB_ROOT=${WB_ROOT:-$HOME/.local/share/workmesh}
PROFILE=${PROFILE:-research}             # minimal | research | full
WB_NODE_NAME=${WB_NODE_NAME:-$(hostname -s)}
LOGIN=auto                              # auto (TTY only) | yes | no
SYSTEM_PACKAGES=auto                    # off for a prebuilt image without sudo
DOCKER_MODE=auto                        # host | client | external | off | auto
# export DOCKER_HOST=ssh://docker-host.example.ts.net
ISOLATION=auto                          # install runsc; kata uses an existing host runtime

TS_ENABLED=yes
TS_MODE=auto                            # kernel | userspace | existing | auto
TS_ACCEPT_DNS=auto                      # MagicDNS on for new kernel nodes; userspace uses proxies
# TS_AUTHKEY_FILE=/run/secrets/tailscale-authkey
# TS_TAGS=tag:research                   # must be allowed by your tailnet policy
# TS_SOCKET=/path/to/existing/tailscaled.sock

# Every local node gets its own durable identity; never copy private node keys.
# The default is an isolated private node until you supply real peer keys.
CAIRN_MODE=node                         # node | worker | off
CAIRN_HTTP_PORT=18080
CAIRN_P2P_PORT=19000
CAIRN_HTTP_BIND=127.0.0.1                # tailnet for remote workers on a kernel interface
CAIRN_P2P_BIND=tailnet                   # auto falls back to loopback in userspace
CAIRN_BOOTSTRAP_FILES=()
# CAIRN_BOOTSTRAP_DIR=/run/config/cairn-peers
# CAIRN_BOOTSTRAP_FILES=(/run/config/leader.json /run/config/desktop.json)
# CAIRN_PEERS=bootstrap                  # private mode's default allowlist
CAIRN_AGENT=auto                        # Linux only by default
CAIRN_AGENT_SANDBOX=auto                 # runsc | kata | bwrap | strongest | none
CAIRN_PARALLEL=1
# CAIRN_NODE_URL=http://cairn-leader.example.ts.net:18080
# CAIRN_FLEET_FILE=/run/secrets/cairn-member.json
# CAIRN_FLEET_IDENTITY=/run/secrets/cairn-leader.identity.json  # leader only

# Use one existing leader for shared tasks. A daemon per machine is an optional
# second topology: Conductor peer links do not replicate task databases.
CONDUCTOR_MODE=auto                      # client if endpoint set; otherwise local
CONDUCTOR_PROJECT=workspace              # set your actual project slug
# CONDUCTOR_ENDPOINT=https://conductor.example.ts.net
# CONDUCTOR_TOKEN_FILE=/run/secrets/conductor-token
# CONDUCTOR_CA_CERT=/run/config/conductor-ca.pem
# CONDUCTOR_HTTP_PROXY=tailnet           # userspace proxy, preserves HTTPS hostname
# DATABASE_URL_FILE=/run/secrets/conductor-database-url       # local/peer only
CONDUCTOR_PORT=18081
CONDUCTOR_INTEGRATE=yes                  # global MCP + supported hooks/rules

# For CONDUCTOR_MODE=peer, use certificates issued by the existing mesh CA.
# CONDUCTOR_BIND=100.101.102.103          # actual kernel Tailscale IP
# CONDUCTOR_PEER_CA=/run/config/mesh-ca.pem
# CONDUCTOR_PEER_CERT=/run/secrets/this-node-cert.pem
# CONDUCTOR_PEER_KEY=/run/secrets/this-node-key.pem
# CONDUCTOR_PEERS=leader=https://leader.example.ts.net:8443
# CONDUCTOR_PEER_DISCOVER_DNS=_conductor-mesh._tcp.mesh.internal
# CONDUCTOR_PEER_DNS_SERVER=100.101.102.104:15353

# Optional userspace TCP bridges. Every listener is on local loopback. Use these
# local addresses in Cairn bootstrap files / CAIRN_NODE_URL. Preserve HTTPS
# hostname validation when forwarding a TLS service; see README.
TAILNET_FORWARDS=()
# TAILNET_FORWARDS=("28080=cairn-leader.example.ts.net:18080" "29000=cairn-peer.example.ts.net:19000")

CLAUDE_RC=auto                          # yes requires login; no disables
CODEX_RC=auto
INSTALL_CLIS=yes                        # Claude, Codex, Cursor CLI, OpenCode v1
INSTALL_CLOUD_TOOLS=yes                  # Modal, RunPod, AWS, Hugging Face
INSTALL_AGENT_STACK=no                  # crypto-autoresearcher API-direct stack, separate venv
INSTALL_CUDA=no                         # yes: separate conda CUDA toolkit, no driver
# CUDA_VERSION=13.3                      # choose a toolkit your host driver supports
INSTALL_LEAN=no                         # repo pins leanprover/lean4:v4.35.0
INSTALL_TPU=no                          # separate JAX 0.4.35 CPU environment
SAGE_MODE=stock                         # stock | patched | off
# SAGE_MODE=patched
# SAGE_LAUNCHER=/path/to/cryptanalysis/sage

# Pins. latest resolves upstream at installation time; resolved science packages
# are exported under state/. Image builds are the preferred reproducibility unit.
CAIRN_VERSION=latest
CONDUCTOR_INSTALL=auto                   # fallback to reviewed source if assets absent
CONDUCTOR_REF=d99a2bbb23d5e59862d7614886e414c95c3dfe13
CONDUCTOR_VERSION=latest
MSOLVE_VERSION=v0.11.0
MSOLVE_SHA256=e33928d8d0b064496ec750c7ee5ff4782fda362a0857a729d9761f93dbf259b5
NODE_VERSION=lts
GO_VERSION=latest
RUST_TOOLCHAIN=stable
CODEX_VERSION=latest
CLAUDE_VERSION=latest
OPENCODE_VERSION=latest

# Supported secret references (contents are not put in process arguments):
# OPENAI_API_KEY_FILE=/run/secrets/openai-key
# ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic-key
# CURSOR_API_KEY_FILE=/run/secrets/cursor-key
# Existing standard environment variables and CLI login files also work.
