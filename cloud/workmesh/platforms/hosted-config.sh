# shellcheck shell=bash disable=SC2034
# Example for Modal and restricted RunPod/coding containers.
# Inject TS_AUTHKEY, CONDUCTOR_ENDPOINT, CONDUCTOR_TOKEN and CAIRN_LEADER_HOST
# through provider secrets. Their values are not embedded in this file.
PROFILE=research
LOGIN=no
SYSTEM_PACKAGES=off
DOCKER_MODE=client
TS_MODE=userspace
CONDUCTOR_MODE=client
: "${CONDUCTOR_ENDPOINT:?Set the existing Conductor HTTPS origin}"
CONDUCTOR_PROJECT=${CONDUCTOR_PROJECT:-crypto}
CONDUCTOR_HTTP_PROXY=tailnet
CAIRN_MODE=worker
CAIRN_AGENT=yes
CAIRN_AGENT_SANDBOX=${CAIRN_AGENT_SANDBOX:-auto}
: "${CAIRN_LEADER_HOST:?Set the Cairn leader tailnet hostname}"
TAILNET_FORWARDS=("28080=$CAIRN_LEADER_HOST:${CAIRN_LEADER_PORT:-18080}")
CAIRN_NODE_URL=http://127.0.0.1:28080
CLAUDE_RC=auto
CODEX_RC=auto
