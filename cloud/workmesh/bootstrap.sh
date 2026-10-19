#!/usr/bin/env bash
# Portable research workspace installer and launcher. Bash 3.2+; Linux/macOS.
# This file is self-contained: downloading bootstrap.sh is sufficient.
set -eo pipefail
umask 077

die() { printf 'workmesh: %s\n' "$*" >&2; exit 1; }
say() { printf 'workmesh: %s\n' "$*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }
DRY_RUN=0
INSTALL_ON_RUN=no
COMMAND=bootstrap
CONFIG=
WORK_DIR=$PWD
CHILD=()

usage() {
  cat <<'EOF'
Usage: bash bootstrap.sh [command] [options] [-- command args...]

  bootstrap     Install tools, start configured nodes, and offer login (default)
  install       Install tools only; suitable for image builds
  up            Start configured services without installing
  login         Vendor/browser login in this terminal
  remote        Start Claude and Codex Remote Control after login
  run           Start services, run command, forward signals, stop owned services
  doctor        Check tools, services, mesh and isolation; nonzero if incomplete
  stop          Stop this installation's services; preserve data and credentials
  plan          Show configuration and planned actions; no writes or network
  export-peer   Export Cairn's public transport key and seed-list entry

Options:
  --config FILE      Source an explicitly trusted Bash configuration file
  --root DIR         Persistent installation/state directory
  --work-dir DIR     Repository working directory (default: current directory)
  --profile NAME     minimal | research | full (default: research)
  --dry-run          No writes, network requests, installs, login or services
  --login           Offer interactive login during bootstrap
  --no-login        Skip interactive login
  --install         Install tools before `run` (otherwise `run` uses an image)
  -h, --help         Show help

Install stages never run project scripts or start experiments. Use `run -- ...`
as an entrypoint. Config/environment values and *_FILE secret references are
documented in README.md and config.example.sh. No credentials belong in URLs.
EOF
}

# Parse twice so command-line values take precedence over a selected config.
ORIGINAL_ARGS=("$@")
parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      bootstrap|install|up|login|remote|run|doctor|stop|plan|export-peer) COMMAND=$1; shift ;;
      --config) [ "$#" -ge 2 ] || die '--config requires a file'; CONFIG=$2; shift 2 ;;
      --root) [ "$#" -ge 2 ] || die '--root requires a directory'; WB_ROOT=$2; shift 2 ;;
      --work-dir) [ "$#" -ge 2 ] || die '--work-dir requires a directory'; WORK_DIR=$2; shift 2 ;;
      --profile) [ "$#" -ge 2 ] || die '--profile requires a name'; PROFILE=$2; shift 2 ;;
      --dry-run) DRY_RUN=1; shift ;;
      --login) LOGIN=yes; shift ;;
      --no-login) LOGIN=no; shift ;;
      --install) INSTALL_ON_RUN=yes; shift ;;
      --) shift; CHILD=("$@"); break ;;
      -h|--help) usage; exit 0 ;;
      *) die "unknown argument: $1" ;;
    esac
  done
}
parse_args "$@"
if [ -n "$CONFIG" ]; then
  [ -r "$CONFIG" ] || die 'configuration file is not readable'
  CONFIG=$(cd "$(dirname "$CONFIG")" && printf '%s/%s' "$PWD" "$(basename "$CONFIG")")
  # shellcheck disable=SC1090
  . "$CONFIG"
fi
parse_args "${ORIGINAL_ARGS[@]}"

WB_ROOT=${WB_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/workmesh}
case "$WB_ROOT" in /*) ;; *) WB_ROOT=$PWD/$WB_ROOT ;; esac
case "$WORK_DIR" in /*) ;; *) WORK_DIR=$PWD/$WORK_DIR ;; esac
case "$WB_ROOT$WORK_DIR" in *$'\n'*|*$'\r'*) die 'paths must not contain newlines' ;; esac
PROFILE=${PROFILE:-research}
LOGIN=${LOGIN:-auto}
SYSTEM_PACKAGES=${SYSTEM_PACKAGES:-auto}
DOCKER_MODE=${DOCKER_MODE:-auto}
ISOLATION=${ISOLATION:-auto}
TS_MODE=${TS_MODE:-auto}
TS_ENABLED=${TS_ENABLED:-yes}
TS_AUTHKEY_FILE=${TS_AUTHKEY_FILE:-}
TS_SOCKET=${TS_SOCKET:-}
TS_TAGS=${TS_TAGS:-}
TS_ACCEPT_DNS=${TS_ACCEPT_DNS:-auto}
TS_SOCKS_PORT=${TS_SOCKS_PORT:-1055}
TS_HTTP_PORT=${TS_HTTP_PORT:-1056}
CAIRN_MODE=${CAIRN_MODE:-node}
CAIRN_HTTP_PORT=${CAIRN_HTTP_PORT:-18080}
CAIRN_P2P_PORT=${CAIRN_P2P_PORT:-19000}
CAIRN_HTTP_BIND=${CAIRN_HTTP_BIND:-127.0.0.1}
CAIRN_P2P_BIND=${CAIRN_P2P_BIND:-tailnet}
CAIRN_AGENT=${CAIRN_AGENT:-auto}
CAIRN_AGENT_SANDBOX=${CAIRN_AGENT_SANDBOX:-auto}
CAIRN_PARALLEL=${CAIRN_PARALLEL:-1}
CONDUCTOR_MODE=${CONDUCTOR_MODE:-auto}
CONDUCTOR_PORT=${CONDUCTOR_PORT:-18081}
CONDUCTOR_PROJECT=${CONDUCTOR_PROJECT:-workspace}
CONDUCTOR_INTEGRATE=${CONDUCTOR_INTEGRATE:-yes}
CONDUCTOR_HTTP_PROXY=${CONDUCTOR_HTTP_PROXY:-}
case "${CONDUCTOR_ENDPOINT:-}" in *'@'*|*'?'*|*'#'*) die 'CONDUCTOR_ENDPOINT must not contain credentials, query parameters or fragments' ;; esac
CLAUDE_RC=${CLAUDE_RC:-auto}
CODEX_RC=${CODEX_RC:-auto}
INSTALL_CLIS=${INSTALL_CLIS:-no}
INSTALL_CLOUD_TOOLS=${INSTALL_CLOUD_TOOLS:-yes}
INSTALL_LEAN=${INSTALL_LEAN:-no}
INSTALL_TPU=${INSTALL_TPU:-no}
INSTALL_AGENT_STACK=${INSTALL_AGENT_STACK:-no}
INSTALL_CUDA=${INSTALL_CUDA:-no}
CUDA_VERSION=${CUDA_VERSION:-}
MSOLVE_VERSION=${MSOLVE_VERSION:-v0.11.0}
MSOLVE_SHA256=${MSOLVE_SHA256:-e33928d8d0b064496ec750c7ee5ff4782fda362a0857a729d9761f93dbf259b5}
LEAN_TOOLCHAIN=${LEAN_TOOLCHAIN:-leanprover/lean4:v4.35.0}
SAGE_MODE=${SAGE_MODE:-stock}
SAGE_LAUNCHER=${SAGE_LAUNCHER:-}
NODE_VERSION=${NODE_VERSION:-lts}
GO_VERSION=${GO_VERSION:-latest}
RUST_TOOLCHAIN=${RUST_TOOLCHAIN:-stable}
CAIRN_VERSION=${CAIRN_VERSION:-latest}
CONDUCTOR_VERSION=${CONDUCTOR_VERSION:-latest}
CONDUCTOR_INSTALL=${CONDUCTOR_INSTALL:-auto}
CONDUCTOR_REF=${CONDUCTOR_REF:-d99a2bbb23d5e59862d7614886e414c95c3dfe13}
CODEX_VERSION=${CODEX_VERSION:-latest}
CLAUDE_VERSION=${CLAUDE_VERSION:-latest}
OPENCODE_VERSION=${OPENCODE_VERSION:-latest}
MICROMAMBA_VERSION=${MICROMAMBA_VERSION:-latest}
GVISOR_VERSION=${GVISOR_VERSION:-latest}
WB_NODE_NAME=${WB_NODE_NAME:-$(hostname -s 2>/dev/null || hostname)}
BIN_DIR=$WB_ROOT/bin
STATE_DIR=$WB_ROOT/state
CACHE_DIR=$WB_ROOT/cache
TOOLS_DIR=$WB_ROOT/tools
MAMBA_ROOT_PREFIX=$WB_ROOT/mamba
SCIENCE_ENV=$MAMBA_ROOT_PREFIX/envs/research
export MAMBA_ROOT_PREFIX
PATH=$BIN_DIR:$TOOLS_DIR/node/bin:$TOOLS_DIR/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH
export PATH
OS=$(uname -s)
MACHINE=$(uname -m)
case "$OS" in Linux) PLATFORM=linux ;; Darwin) PLATFORM=darwin ;; *) die 'use Linux, macOS or WSL2' ;; esac
case "$MACHINE" in x86_64|amd64) ARCH=amd64; CONDA_ARCH=64; RUST_ARCH=x86_64 ;;
  aarch64|arm64) ARCH=arm64; CONDA_ARCH=aarch64; RUST_ARCH=aarch64 ;;
  *) die "unsupported architecture: $MACHINE" ;; esac
case "$PROFILE" in minimal|research|full) ;; *) die 'profile must be minimal, research or full' ;; esac
case "$DOCKER_MODE" in auto|host|client|external|off) ;; *) die 'invalid DOCKER_MODE' ;; esac
case "$ISOLATION" in auto|gvisor|kata|off) ;; *) die 'invalid ISOLATION' ;; esac
case "$TS_MODE" in auto|kernel|userspace|existing) ;; *) die 'invalid TS_MODE' ;; esac
case "$CAIRN_MODE" in node|worker|off) ;; *) die 'invalid CAIRN_MODE' ;; esac
case "$CONDUCTOR_MODE" in auto|local|client|peer|off) ;; *) die 'invalid CONDUCTOR_MODE' ;; esac
case "$SAGE_MODE" in stock|patched|off) ;; *) die 'invalid SAGE_MODE' ;; esac
case "$CAIRN_AGENT_SANDBOX" in auto|strongest|runsc|kata|bwrap|none) ;; *) die 'invalid CAIRN_AGENT_SANDBOX' ;; esac
for port in "$CAIRN_HTTP_PORT" "$CAIRN_P2P_PORT" "$CONDUCTOR_PORT" "$TS_SOCKS_PORT" "$TS_HTTP_PORT"; do
  case "$port" in ''|*[!0-9]*) die 'ports must be integers' ;; esac
  [ "$port" -gt 0 ] && [ "$port" -le 65535 ] || die 'port out of range'
done
[ "$CAIRN_HTTP_PORT" != "$CONDUCTOR_PORT" ] || die 'Cairn and Conductor need different ports'
case "$WB_NODE_NAME" in ''|*[!a-zA-Z0-9._-]*) die 'WB_NODE_NAME must be a hostname' ;; esac
CONTAINER=no
if [ -f /.dockerenv ] || [ -f /run/.containerenv ] || [ -n "${MODAL_TASK_ID:-}${RUNPOD_POD_ID:-}" ]; then CONTAINER=yes; fi
if [ -f /etc/codex/network-policy.json ] || { have systemd-detect-virt && systemd-detect-virt --container --quiet; }; then CONTAINER=yes; fi
[ -z "${WB_CONTAINER:-}" ] || CONTAINER=$WB_CONTAINER
if [ "$CONDUCTOR_MODE" = auto ]; then
  if [ -n "${CONDUCTOR_ENDPOINT:-}" ]; then CONDUCTOR_MODE=client; else CONDUCTOR_MODE=local; fi
fi

plan() {
  cat <<EOF
Platform: $PLATFORM/$ARCH; container: $CONTAINER; profile: $PROFILE
Persistent root: $WB_ROOT
Working directory: $WORK_DIR
System packages: $SYSTEM_PACKAGES; Docker: $DOCKER_MODE; isolation: $ISOLATION
Tailscale: $TS_ENABLED / $TS_MODE (existing connections reused)
Cairn: $CAIRN_MODE; API port $CAIRN_HTTP_PORT; P2P port $CAIRN_P2P_PORT
Cairn host agent: $CAIRN_AGENT; sandbox preference: $CAIRN_AGENT_SANDBOX
Conductor: $CONDUCTOR_MODE; local API port $CONDUCTOR_PORT
Coding CLIs: $INSTALL_CLIS; integration: $CONDUCTOR_INTEGRATE
Remote Control: Claude=$CLAUDE_RC, Codex=$CODEX_RC (requires vendor login)
Sage: $SAGE_MODE; Lean: $INSTALL_LEAN; separate JAX/TPU environment: $INSTALL_TPU
Install: native build tools, Rust, Go, Node; research adds Sage/PARI/Singular,
msolve, lattice tools, Python science, SAT and lint tools, cloud SDKs.
Services start only for bootstrap/up/run/remote. Credentials are not shown.
EOF
}
if [ "$COMMAND" = plan ] || [ "$DRY_RUN" = 1 ]; then plan; exit 0; fi

# Secret references are consumed only for real execution; never written into argv.
secret_file() {
  local variable=$1 reference=$2 value
  [ -n "$reference" ] || return 0
  [ -r "$reference" ] || die "$variable file is not readable"
  value=$(cat "$reference")
  [ -n "$value" ] || die "$variable file is empty"
  printf -v "$variable" '%s' "$value"
  export "${variable?}"
}
load_secrets() {
secret_file DATABASE_URL "${DATABASE_URL_FILE:-}"
secret_file CONDUCTOR_TOKEN "${CONDUCTOR_TOKEN_FILE:-}"
secret_file OPENAI_API_KEY "${OPENAI_API_KEY_FILE:-}"
secret_file ANTHROPIC_API_KEY "${ANTHROPIC_API_KEY_FILE:-}"
secret_file CURSOR_API_KEY "${CURSOR_API_KEY_FILE:-}"
}

ensure_dirs() { mkdir -p "$BIN_DIR" "$STATE_DIR/services" "$STATE_DIR/logs" "$CACHE_DIR" "$TOOLS_DIR"; chmod 700 "$STATE_DIR"; }
TMP_DIR=
STARTED_SERVICES=()
SERVICE_LOCKS=()
NEW_CONDUCTOR=no
cleanup() {
  local lock
  for lock in "${SERVICE_LOCKS[@]}"; do rmdir "$lock" 2>/dev/null || true; done
  [ -z "$TMP_DIR" ] || rm -rf "$TMP_DIR"
}
trap cleanup EXIT
temp_dir() { [ -n "$TMP_DIR" ] || TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/workmesh.XXXXXX"); }
fetch() { curl --fail --location --silent --show-error --retry 3 --connect-timeout 15 --max-time 600 --proto '=https' --proto-redir '=https' "$1" -o "$2"; }
sha256() { if have sha256sum; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }
verify() { [ "$(sha256 "$1")" = "$2" ] || die 'download checksum mismatch'; }
as_root() { if [ "$(id -u)" = 0 ]; then "$@"; elif have sudo; then sudo -n "$@"; else die 'system setup needs root or passwordless sudo; use SYSTEM_PACKAGES=off with a prepared image'; fi; }
PYTHON=
python_cmd() { if [ -n "$PYTHON" ]; then "$PYTHON" "$@"; elif have python3; then python3 "$@"; else die 'Python 3 is required (run install first)'; fi; }

install_system() {
  [ "$SYSTEM_PACKAGES" != off ] || return 0
  say 'Installing native build prerequisites'
  if [ "$PLATFORM" = darwin ]; then
    have brew || die 'install Homebrew first, or set SYSTEM_PACKAGES=off on a prepared Mac'
    brew install cmake ninja pkgconf git curl jq tmux python gmp mpfr libmpc flint ntl fplll openssl@3 shellcheck autoconf automake libtool llvm libomp
  elif have apt-get; then
    as_root apt-get update -qq
    as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates curl git jq tar unzip xz-utils bzip2 build-essential cmake ninja-build \
      pkg-config python3 python3-venv python3-dev libssl-dev libffi-dev zlib1g-dev \
      libgmp-dev libmpfr-dev libmpc-dev libflint-dev libntl-dev libfplll-dev \
      libopenblas-dev tmux openssh-client bubblewrap autoconf automake libtool
    if [ "$PROFILE" = full ]; then
      as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        clang clang-tidy clang-format cppcheck shellcheck valgrind gdb gcovr \
        latexmk texlive-latex-extra texlive-science texlive-fonts-recommended \
        texlive-bibtex-extra poppler-utils
    fi
  elif have dnf; then
    as_root dnf install -y ca-certificates curl git jq tar unzip xz bzip2 gcc gcc-c++ make \
      cmake ninja-build pkgconf-pkg-config python3 python3-pip python3-devel openssl-devel \
      libffi-devel zlib-devel gmp-devel mpfr-devel tmux openssh-clients autoconf automake libtool
    # FLINT/NTL/fplll and science tools come from conda-forge on RPM hosts.
  else
    die 'no supported package manager; use Debian/Ubuntu, an RPM host, macOS, or SYSTEM_PACKAGES=off'
  fi
}

install_rust() {
  if have rustc && have cargo; then say 'Rust already installed (retained)'; return; fi
  temp_dir
  local target
  if [ "$PLATFORM" = darwin ]; then target=$RUST_ARCH-apple-darwin; else target=$RUST_ARCH-unknown-linux-gnu; fi
  fetch "https://static.rust-lang.org/rustup/dist/$target/rustup-init" "$TMP_DIR/rustup-init"
  fetch "https://static.rust-lang.org/rustup/dist/$target/rustup-init.sha256" "$TMP_DIR/rustup.sha256"
  verify "$TMP_DIR/rustup-init" "$(awk '{print $1}' "$TMP_DIR/rustup.sha256")"
  chmod 700 "$TMP_DIR/rustup-init"
  "$TMP_DIR/rustup-init" -y --no-modify-path --profile minimal --default-toolchain "$RUST_TOOLCHAIN" --component rustfmt --component clippy
}

install_go() {
  if have go && [ "$GO_VERSION" = latest ] && go version | python_cmd -c 'import re,sys; m=re.search(r"go(\d+)\.(\d+)",sys.stdin.read()); sys.exit(0 if m and tuple(map(int,m.groups())) >= (1,21) else 1)'; then
    say 'Go already installed; modules retain toolchain selection'
    return
  fi
  temp_dir
  fetch 'https://go.dev/dl/?mode=json&include=all' "$TMP_DIR/go.json"
  local line version filename checksum
  line=$(python_cmd - "$TMP_DIR/go.json" "$PLATFORM" "$ARCH" "$GO_VERSION" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))
for row in rows:
    if (sys.argv[4] == 'latest' and row.get('stable')) or row['version'].removeprefix('go') == sys.argv[4].removeprefix('go'):
        for item in row['files']:
            if item['os'] == sys.argv[2] and item['arch'] == sys.argv[3] and item['kind'] == 'archive':
                print(row['version'], item['filename'], item['sha256']); sys.exit(0)
raise SystemExit('No Go download for the requested platform/version')
PY
)
  read -r version filename checksum <<< "$line"
  if [ -f "$TOOLS_DIR/go/VERSION" ] && [ "$(head -1 "$TOOLS_DIR/go/VERSION")" = "$version" ]; then return; fi
  fetch "https://go.dev/dl/$filename" "$TMP_DIR/go.tar.gz"
  verify "$TMP_DIR/go.tar.gz" "$checksum"
  mkdir -p "$TMP_DIR/go-stage"
  tar -xzf "$TMP_DIR/go.tar.gz" -C "$TMP_DIR/go-stage"
  rm -rf "$TOOLS_DIR/go"
  mv "$TMP_DIR/go-stage/go" "$TOOLS_DIR/go"
}

install_node() {
  if have node && have npm && [ "$NODE_VERSION" = lts ] && [ "$(node -p 'Number(process.versions.node.split(".")[0])')" -ge 20 ]; then return; fi
  temp_dir
  local version filename checksum node_arch node_os
  node_arch=$ARCH; [ "$ARCH" != amd64 ] || node_arch=x64
  node_os=$PLATFORM
  if [ "$NODE_VERSION" = lts ]; then
    fetch 'https://nodejs.org/dist/index.json' "$TMP_DIR/node.json"
    version=$(python_cmd - "$TMP_DIR/node.json" <<'PY'
import json, sys
print(next(row['version'] for row in json.load(open(sys.argv[1])) if row.get('lts')))
PY
)
  else version=v${NODE_VERSION#v}; fi
  filename=node-$version-$node_os-$node_arch.tar.gz
  fetch "https://nodejs.org/dist/$version/SHASUMS256.txt" "$TMP_DIR/node.sha256"
  checksum=$(awk -v name="$filename" '$2 == name {print $1}' "$TMP_DIR/node.sha256")
  [ -n "$checksum" ] || die 'Node release does not contain this platform'
  fetch "https://nodejs.org/dist/$version/$filename" "$TMP_DIR/node.tar.gz"
  verify "$TMP_DIR/node.tar.gz" "$checksum"
  mkdir -p "$TMP_DIR/node-stage"
  tar -xzf "$TMP_DIR/node.tar.gz" -C "$TMP_DIR/node-stage"
  rm -rf "$TOOLS_DIR/node"
  mv "$TMP_DIR/node-stage/node-$version-$node_os-$node_arch" "$TOOLS_DIR/node"
}

install_science() {
  [ "$PROFILE" != minimal ] || return 0
  temp_dir
  local subdir line url checksum
  if [ "$PLATFORM" = darwin ]; then
    if [ "$ARCH" = arm64 ]; then subdir=osx-arm64; else subdir=osx-64; fi
  else subdir=linux-$CONDA_ARCH; fi
  if ! have micromamba; then
    fetch 'https://api.anaconda.org/package/conda-forge/micromamba' "$TMP_DIR/mamba.json"
    line=$(python_cmd - "$TMP_DIR/mamba.json" "$subdir" "$MICROMAMBA_VERSION" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
version = data['latest_version'] if sys.argv[3] == 'latest' else sys.argv[3]
rows = [r for r in data['files'] if r['version'] == version and r['basename'].startswith(sys.argv[2] + '/') and r['basename'].endswith('.tar.bz2')]
if not rows: raise SystemExit('No micromamba build for this platform/version')
row = sorted(rows, key=lambda x: x.get('upload_time', ''))[-1]
digest = row.get('sha256') or row.get('attrs', {}).get('sha256')
if not digest: raise SystemExit('micromamba package has no SHA256')
print('https://api.anaconda.org/download/conda-forge/micromamba/' + version + '/' + row['basename'], digest)
PY
)
    read -r url checksum <<< "$line"
    fetch "$url" "$TMP_DIR/mamba.tar.bz2"
    verify "$TMP_DIR/mamba.tar.bz2" "$checksum"
    mkdir -p "$TMP_DIR/mamba-stage"
    tar -xjf "$TMP_DIR/mamba.tar.bz2" -C "$TMP_DIR/mamba-stage" bin/micromamba
    install -m 755 "$TMP_DIR/mamba-stage/bin/micromamba" "$BIN_DIR/micromamba"
  fi
  local specs=(python=3.12 pip numpy scipy sympy matplotlib pandas networkx pyyaml pytest \
    gmpy2 python-flint fpylll cypari2 cysignals pari singular libflint ntl fplll \
    ipython jupyterlab requests tqdm ruff mypy z3-solver)
  [ "$SAGE_MODE" != stock ] || specs+=(sage)
  # A spec hash avoids re-solving on every startup while preserving explicit exports.
  local digest marker
  digest=$(printf '%s\n' "${specs[@]}" | cksum | awk '{print $1}')
  marker=$SCIENCE_ENV/.workmesh-spec
  if [ ! -f "$marker" ] || [ "$(cat "$marker")" != "$digest" ]; then
    micromamba create -y -p "$SCIENCE_ENV" -c conda-forge --strict-channel-priority "${specs[@]}"
    "$SCIENCE_ENV/bin/python" -m pip install 'python-sat==1.9.dev15' 'pycryptosat==5.15.0'
    printf '%s\n' "$digest" > "$marker"
    micromamba list -p "$SCIENCE_ENV" --explicit > "$STATE_DIR/research-explicit.txt"
    "$SCIENCE_ENV/bin/python" -m pip freeze > "$STATE_DIR/research-pip.txt"
  fi
  if [ "$INSTALL_TPU" = yes ]; then
    micromamba create -y -p "$MAMBA_ROOT_PREFIX/envs/tpu" -c conda-forge python=3.12 pip
    "$MAMBA_ROOT_PREFIX/envs/tpu/bin/python" -m pip install 'jax==0.4.35' 'jaxlib==0.4.35' 'numpy>=1.26' 'pytest>=8'
  fi
}

install_msolve() {
  [ "$PROFILE" != minimal ] || return 0
  have msolve && return 0
  temp_dir
  fetch "https://github.com/algebraic-solving/msolve/releases/download/$MSOLVE_VERSION/msolve-${MSOLVE_VERSION#v}.tar.gz" "$TMP_DIR/msolve.tar.gz"
  verify "$TMP_DIR/msolve.tar.gz" "$MSOLVE_SHA256"
  mkdir -p "$TMP_DIR/msolve-source"
  tar -xzf "$TMP_DIR/msolve.tar.gz" -C "$TMP_DIR/msolve-source" --strip-components=1
  (
    cd "$TMP_DIR/msolve-source"
    local prefix=$SCIENCE_ENV compiler=${CC:-cc}
    if [ "$PLATFORM" = darwin ]; then
      compiler=$(brew --prefix llvm)/bin/clang
      prefix=$(brew --prefix)
      CFLAGS="${CFLAGS:-} -I$(brew --prefix libomp)/include"
      LDFLAGS="${LDFLAGS:-} -L$(brew --prefix libomp)/lib"
      export CFLAGS LDFLAGS
    fi
    export CC=$compiler
    export CPPFLAGS="${CPPFLAGS:-} -I$prefix/include"
    export LDFLAGS="${LDFLAGS:-} -L$prefix/lib -Wl,-rpath,$prefix/lib"
    [ -x ./configure ] || ./autogen.sh
    ./configure --prefix="$WB_ROOT"
    make -j"${BUILD_JOBS:-2}"
    make install
  )
  printf '%s %s\n' "$MSOLVE_VERSION" "$MSOLVE_SHA256" > "$STATE_DIR/msolve.version"
}

install_cuda() {
  [ "$INSTALL_CUDA" = yes ] || return 0
  [ "$PLATFORM" = linux ] || die 'CUDA toolkit requires a supported Linux NVIDIA host'
  have micromamba || die 'INSTALL_CUDA=yes requires the research or full profile'
  local spec=cuda-toolkit
  [ -z "$CUDA_VERSION" ] || spec=cuda-toolkit=$CUDA_VERSION
  micromamba create -y -p "$MAMBA_ROOT_PREFIX/envs/cuda" -c nvidia -c conda-forge "$spec"
}

install_cloud_tools() {
  [ "$INSTALL_CLOUD_TOOLS" = yes ] || return 0
  local venv=$TOOLS_DIR/cloud
  if [ -x "$SCIENCE_ENV/bin/python" ]; then venv=$SCIENCE_ENV; else
    [ -x "$venv/bin/python" ] || python_cmd -m venv "$venv"
  fi
  "$venv/bin/python" -m pip install --upgrade pip
  "$venv/bin/python" -m pip install modal runpod boto3 awscli huggingface-hub pyyaml
}

install_agent_stack() {
  [ "$INSTALL_AGENT_STACK" = yes ] || return 0
  local venv=$TOOLS_DIR/api-agent
  [ -x "$venv/bin/python" ] || python_cmd -m venv "$venv"
  "$venv/bin/python" -m pip install 'langgraph>=1.0,<2' 'langchain-core>=1.0,<2' \
    'langgraph-checkpoint-sqlite>=3.0,<4' 'PyYAML>=6.0' 'sympy>=1.12' 'numpy>=1.26' 'pytest>=8.0'
  printf '#!/usr/bin/env bash\nexec %q "$@"\n' "$venv/bin/python" > "$BIN_DIR/api-agent-python"
  chmod 755 "$BIN_DIR/api-agent-python"
}

release_tag() {
  local repo=$1 requested=$2 resolved
  if [ "$requested" != latest ]; then printf '%s\n' "$requested"; return; fi
  resolved=$(curl --fail --silent --show-error --location --head --proto '=https' --proto-redir '=https' --connect-timeout 15 --max-time 60 --output /dev/null --write-out '%{url_effective}' "https://github.com/$repo/releases/latest")
  case "$resolved" in */releases/tag/*) printf '%s\n' "${resolved##*/}" ;; *) die "cannot resolve release for $repo" ;; esac
}

install_nodes() {
  temp_dir
  local version asset target checksum
  if [ "$CAIRN_MODE" != off ] || [ "$CAIRN_AGENT" = yes ]; then
    version=$(release_tag aburan28/cairn "$CAIRN_VERSION")
    if [ ! -f "$STATE_DIR/cairn.version" ] || [ "$(cat "$STATE_DIR/cairn.version")" != "$version" ] || [ ! -x "$BIN_DIR/cairn" ]; then
      if [ "$PLATFORM" = darwin ]; then target=$RUST_ARCH-apple-darwin; else target=$RUST_ARCH-unknown-linux-musl; fi
      asset=cairn-$version-$target.tar.gz
      fetch "https://github.com/aburan28/cairn/releases/download/$version/$asset" "$TMP_DIR/cairn.tar.gz"
      fetch "https://github.com/aburan28/cairn/releases/download/$version/$asset.sha256" "$TMP_DIR/cairn.sha256"
      verify "$TMP_DIR/cairn.tar.gz" "$(awk 'NR == 1 {print $1}' "$TMP_DIR/cairn.sha256")"
      mkdir -p "$TMP_DIR/cairn-release"
      tar -xzf "$TMP_DIR/cairn.tar.gz" -C "$TMP_DIR/cairn-release" cairn
      install -m 755 "$TMP_DIR/cairn-release/cairn" "$BIN_DIR/cairn"
      printf '%s\n' "$version" > "$STATE_DIR/cairn.version"
    fi
  fi
  if [ "$CONDUCTOR_MODE" != off ]; then
    case "$CONDUCTOR_INSTALL" in auto|release|source) ;; *) die 'CONDUCTOR_INSTALL must be auto, release or source' ;; esac
    if [ "$CONDUCTOR_INSTALL" = source ]; then version=source; else version=$(release_tag aburan28/conductor "$CONDUCTOR_VERSION"); fi
    local use_source=no
    if [ "$CONDUCTOR_INSTALL" = source ]; then use_source=yes
    elif [ "$CONDUCTOR_INSTALL" = auto ]; then
      asset=conductor_${version}_${PLATFORM}_${ARCH}.tar.gz
      if ! curl --fail --silent --head --location --proto '=https' --proto-redir '=https' --max-time 30 "https://github.com/aburan28/conductor/releases/download/$version/$asset" -o /dev/null; then use_source=yes; fi
    fi
    if [ "$use_source" = yes ]; then
      if [ ! -f "$STATE_DIR/conductor.version" ] || [ "$(cat "$STATE_DIR/conductor.version")" != "source:$CONDUCTOR_REF" ] || [ ! -x "$BIN_DIR/conductor" ]; then
        say "Building Conductor from reviewed ref $CONDUCTOR_REF (release assets unavailable or source selected)"
        git init -q "$TMP_DIR/conductor-source"
        (
          cd "$TMP_DIR/conductor-source"
          git remote add origin https://github.com/aburan28/conductor.git
          git fetch --depth 1 origin "$CONDUCTOR_REF"
          git checkout -q --detach FETCH_HEAD
          GOBIN=$BIN_DIR go install ./cmd/conductor ./cmd/conductord ./cmd/conductor-mcp
        )
        printf 'source:%s\n' "$CONDUCTOR_REF" > "$STATE_DIR/conductor.version"
      fi
      return
    fi
    if [ ! -f "$STATE_DIR/conductor.version" ] || [ "$(cat "$STATE_DIR/conductor.version")" != "$version" ] || [ ! -x "$BIN_DIR/conductor" ]; then
      asset=conductor_${version}_${PLATFORM}_${ARCH}.tar.gz
      fetch "https://github.com/aburan28/conductor/releases/download/$version/$asset" "$TMP_DIR/conductor.tar.gz"
      fetch "https://github.com/aburan28/conductor/releases/download/$version/SHA256SUMS" "$TMP_DIR/conductor.sha256"
      checksum=$(awk -v name="$asset" '$2 == name {print $1}' "$TMP_DIR/conductor.sha256")
      [ -n "$checksum" ] || die 'Conductor checksum entry is missing'
      verify "$TMP_DIR/conductor.tar.gz" "$checksum"
      mkdir -p "$TMP_DIR/conductor-release"
      tar -xzf "$TMP_DIR/conductor.tar.gz" -C "$TMP_DIR/conductor-release"
      for program in conductor conductord conductor-mcp; do
        install -m 755 "$TMP_DIR/conductor-release/conductor_${version}_${PLATFORM}_${ARCH}/$program" "$BIN_DIR/$program"
      done
      printf '%s\n' "$version" > "$STATE_DIR/conductor.version"
    fi
  fi
}

install_clis() {
  [ "$INSTALL_CLIS" = yes ] || return 0
  if ! have codex || [ "$CODEX_VERSION" != latest ]; then npm install --global --prefix "$WB_ROOT" "@openai/codex@$CODEX_VERSION"; fi
  if ! have opencode || [ "$OPENCODE_VERSION" != latest ]; then npm install --global --prefix "$WB_ROOT" "opencode-ai@$OPENCODE_VERSION"; fi
  temp_dir
  if ! have claude || [ "$CLAUDE_VERSION" != latest ]; then
    fetch 'https://claude.ai/install.sh' "$TMP_DIR/claude-install.sh"
    bash "$TMP_DIR/claude-install.sh" "$CLAUDE_VERSION"
  fi
  if ! have cursor-agent && [ ! -x "$HOME/.local/bin/agent" ]; then
    fetch 'https://cursor.com/install' "$TMP_DIR/cursor-install.sh"
    bash "$TMP_DIR/cursor-install.sh"
  fi
  if [ "$INSTALL_LEAN" = yes ] && ! have elan; then
    fetch 'https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh' "$TMP_DIR/elan-init.sh"
    bash "$TMP_DIR/elan-init.sh" -y --no-modify-path --default-toolchain "$LEAN_TOOLCHAIN"
  fi
}

install_tailscale() {
  [ "$TS_ENABLED" != no ] || return 0
  have tailscale && return 0
  if [ "$PLATFORM" = darwin ]; then
    [ "$SYSTEM_PACKAGES" != off ] || die 'install and authenticate system Tailscale on this prepared Mac first'
    brew install tailscale
    return
  fi
  temp_dir
  local file checksum
  fetch 'https://pkgs.tailscale.com/stable/?mode=json' "$TMP_DIR/tailscale.json"
  file=$(python_cmd - "$TMP_DIR/tailscale.json" "$ARCH" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))['Tarballs'][sys.argv[2]])
PY
)
  fetch "https://pkgs.tailscale.com/stable/$file.sha256" "$TMP_DIR/tailscale.sha256"
  checksum=$(awk 'NR == 1 {print $1}' "$TMP_DIR/tailscale.sha256")
  fetch "https://pkgs.tailscale.com/stable/$file" "$TMP_DIR/tailscale.tgz"
  verify "$TMP_DIR/tailscale.tgz" "$checksum"
  mkdir -p "$TMP_DIR/ts-stage"
  tar -xzf "$TMP_DIR/tailscale.tgz" -C "$TMP_DIR/ts-stage" --strip-components=1
  install -m 755 "$TMP_DIR/ts-stage/tailscale" "$BIN_DIR/tailscale"
  install -m 755 "$TMP_DIR/ts-stage/tailscaled" "$BIN_DIR/tailscaled"
}

install_docker() {
  [ "$DOCKER_MODE" != off ] || return 0
  if [ "$PLATFORM" = darwin ]; then
    have docker || brew install docker docker-compose
    say 'Use a running Docker Desktop/Colima VM, or a remote DOCKER_HOST on macOS'
    return
  fi
  if ! have docker; then
    [ "$SYSTEM_PACKAGES" != off ] || die 'Docker CLI is missing from this prepared image; install it or set DOCKER_MODE=off'
    if have apt-get; then
      as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends docker.io
    elif have dnf; then
      if dnf info docker >/dev/null 2>&1; then as_root dnf install -y docker; else as_root dnf install -y moby-engine; fi
    else die 'install a Docker client in the prepared image'; fi
  fi
  case "$DOCKER_MODE" in client|external) return ;; esac
  if [ "$CONTAINER" = yes ]; then
    [ "$DOCKER_MODE" != host ] || die 'DOCKER_MODE=host needs a VM/bare-metal host, not a nested container'
    say 'Container detected: Docker CLI installed; use an existing engine or DOCKER_HOST'
    return
  fi
  if have systemctl && [ -d /run/systemd/system ]; then as_root systemctl enable --now docker; fi
}

install_isolation() {
  [ "$ISOLATION" != off ] || return 0
  [ "$PLATFORM" = linux ] || { say 'gVisor/Kata require Linux; retaining macOS isolation'; return; }
  if [ "$ISOLATION" = kata ]; then
    [ -c /dev/kvm ] || die 'Kata requires /dev/kvm and nested virtualization'
    have containerd-shim-kata-v2 || have kata-runtime || die 'install the host-specific Kata package and configure its OCI runtime first; see README'
    return
  fi
  # Installing a userspace runtime needs no Docker daemon or kernel modules.
  if ! have runsc; then
    temp_dir
    local base runsc_arch
    runsc_arch=$RUST_ARCH
    base=https://storage.googleapis.com/gvisor/releases/release/$GVISOR_VERSION/$runsc_arch
    fetch "$base/runsc" "$TMP_DIR/runsc"
    fetch "$base/runsc.sha512" "$TMP_DIR/runsc.sha512"
    python_cmd - "$TMP_DIR/runsc" "$TMP_DIR/runsc.sha512" <<'PY'
import hashlib, sys
with open(sys.argv[1], 'rb') as f: digest = hashlib.sha512(f.read()).hexdigest()
if digest != open(sys.argv[2]).read().split()[0]: raise SystemExit('gVisor checksum mismatch')
PY
    install -m 755 "$TMP_DIR/runsc" "$BIN_DIR/runsc"
  fi
  # Do not edit daemon.json or restart another user's Docker service. Host admin
  # can register this runtime with `sudo /absolute/path/runsc install`.
}

write_environment() {
  local envfile=$WB_ROOT/env.sh
  {
    printf '# Source this file to use this installation. No secrets.\n'
    printf 'export WORKMESH_ROOT=%q\n' "$WB_ROOT"
    printf 'export MAMBA_ROOT_PREFIX=%q\n' "$MAMBA_ROOT_PREFIX"
    printf 'export PATH=%q:"$PATH"\n' "$BIN_DIR:$TOOLS_DIR/node/bin:$TOOLS_DIR/go/bin:$TOOLS_DIR/cloud/bin:$HOME/.cargo/bin:$HOME/.elan/bin"
    if [ -d "$SCIENCE_ENV/bin" ]; then printf 'export PATH=%q:"$PATH"\n' "$SCIENCE_ENV/bin"; fi
    if [ -n "$SAGE_LAUNCHER" ]; then printf 'export WORKMESH_SAGE_LAUNCHER=%q\n' "$SAGE_LAUNCHER"; fi
    [ -z "${CONDUCTOR_ENDPOINT:-}" ] || printf 'export CONDUCTOR_ENDPOINT=%q\n' "$CONDUCTOR_ENDPOINT"
    printf 'export CONDUCTOR_PROJECT=%q\n' "$CONDUCTOR_PROJECT"
    [ -z "${CONDUCTOR_CA_CERT:-}" ] || printf 'export CONDUCTOR_CA_CERT=%q\n' "$CONDUCTOR_CA_CERT"
    local reference variable
    for variable in OPENAI_API_KEY ANTHROPIC_API_KEY CURSOR_API_KEY; do
      reference=${variable}_FILE
      reference=${!reference}
      [ -z "$reference" ] || printf 'if [ -z "${%s:-}" ] && [ -r %q ]; then %s=$(cat %q); export %s; fi\n' "$variable" "$reference" "$variable" "$reference" "$variable"
    done
    if [ -d "$MAMBA_ROOT_PREFIX/envs/cuda" ]; then
      printf 'export CUDA_HOME=%q\n' "$MAMBA_ROOT_PREFIX/envs/cuda"
      printf 'export PATH=%q:"$PATH"\n' "$MAMBA_ROOT_PREFIX/envs/cuda/bin"
    fi
  } > "$envfile"
  if [ "$SAGE_MODE" = patched ]; then
    [ -x "$SAGE_LAUNCHER" ] || die 'SAGE_MODE=patched requires an executable checked SAGE_LAUNCHER'
    {
      printf '#!/usr/bin/env bash\nexec %q "$@"\n' "$SAGE_LAUNCHER"
    } > "$BIN_DIR/sage-checked"
    chmod 755 "$BIN_DIR/sage-checked"
  fi
  # shellcheck disable=SC1090
  . "$envfile"
}

activate_paths() {
  PATH=$BIN_DIR:$TOOLS_DIR/node/bin:$TOOLS_DIR/go/bin:$TOOLS_DIR/cloud/bin:$HOME/.cargo/bin:$HOME/.elan/bin:$PATH
  [ ! -d "$SCIENCE_ENV/bin" ] || PATH=$SCIENCE_ENV/bin:$PATH
  if [ -d "$MAMBA_ROOT_PREFIX/envs/cuda/bin" ]; then
    CUDA_HOME=$MAMBA_ROOT_PREFIX/envs/cuda
    PATH=$CUDA_HOME/bin:$PATH
    export CUDA_HOME
  fi
  export PATH
}

conductor_api() {
  local proxy=$CONDUCTOR_HTTP_PROXY
  [ "$proxy" != tailnet ] || proxy=http://127.0.0.1:$TS_HTTP_PORT
  if [ -n "$proxy" ]; then
    env HTTP_PROXY="$proxy" HTTPS_PROXY="$proxy" http_proxy="$proxy" https_proxy="$proxy" conductor "$@"
  else conductor "$@"; fi
}

validate_remote_conductor_endpoint() {
  case "$1" in
    https://?*) ;;
    *)
      # Match the whole loopback authority. A prefix/glob would also accept
      # URL userinfo such as http://localhost:80@attacker.example.
      if [[ "$1" =~ ^http://(localhost|127\.0\.0\.1|\[::1\])(:[0-9]{1,5})?/?$ ]]; then return 0; fi
      die 'remote Conductor endpoints must use HTTPS; HTTP is allowed only on loopback'
      ;;
  esac
}

write_mcp_launcher() {
  local program=$BIN_DIR/conductor-mcp real=$TOOLS_DIR/conductor-mcp.real proxy=$CONDUCTOR_HTTP_PROXY
  [ -x "$program" ] || return 0
  [ "$proxy" != tailnet ] || proxy=http://127.0.0.1:$TS_HTTP_PORT
  if [ -n "$proxy" ]; then
    # A userspace tailnet proxy belongs to this machine; no proxy credentials
    # are serialized into the gateway launcher.
    [[ "$proxy" =~ ^http://(127\.0\.0\.1|localhost):[0-9]+$ ]] || die 'CONDUCTOR_HTTP_PROXY must be a local HTTP proxy URL or tailnet'
  fi
  if ! python_cmd -c 'import sys; raise SystemExit(not open(sys.argv[1],"rb").read(100).startswith(b"#!/usr/bin/env bash\n# workmesh gateway wrapper\n"))' "$program"; then mv "$program" "$real"; fi
  [ -x "$real" ] || die 'Conductor MCP gateway binary is missing; rerun install'
  {
    printf '#!/usr/bin/env bash\n# workmesh gateway wrapper\nset -e\n'
    [ -z "${CONDUCTOR_ENDPOINT:-}" ] || printf 'export CONDUCTOR_ENDPOINT=%q\n' "$CONDUCTOR_ENDPOINT"
    [ -z "${CONDUCTOR_CA_CERT:-}" ] || printf 'export CONDUCTOR_CA_CERT=%q\n' "$CONDUCTOR_CA_CERT"
    if [ -n "${CONDUCTOR_TOKEN_FILE:-}" ]; then
      printf 'CONDUCTOR_TOKEN=$(cat %q); export CONDUCTOR_TOKEN\n' "$CONDUCTOR_TOKEN_FILE"
    fi
    if [ -n "$proxy" ]; then
      printf 'export HTTP_PROXY=%q HTTPS_PROXY=%q http_proxy=%q https_proxy=%q\n' "$proxy" "$proxy" "$proxy" "$proxy"
    fi
    printf 'exec %q "$@"\n' "$real"
  } > "$program"
  chmod 755 "$program"
}

# Services have their own process groups, inherited environment, restart budget,
# launch scripts and private logs. PID + start time + exact launcher path must
# match before any stop signal is sent. No shared system services are stopped.
write_supervisor() {
  cat > "$STATE_DIR/services/supervisor.py" <<'PY'
import json, os, signal, subprocess, sys, time
launcher, record = sys.argv[1:]
os.setsid()
def stamp(pid):
    return subprocess.check_output(['ps', '-p', str(pid), '-o', 'lstart='], text=True).strip()
with open(record, 'w') as f:
    json.dump({'pid': os.getpid(), 'start': stamp(os.getpid()), 'launcher': launcher}, f)
child = None
stopping = False
def stop(signum, frame):
    global stopping
    stopping = True
    if child and child.poll() is None:
        try: child.send_signal(signum)
        except ProcessLookupError: pass
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
failures = 0
try:
    while not stopping:
        started = time.monotonic()
        child = subprocess.Popen(['bash', launcher])
        code = child.wait()
        if stopping or code == 0: break
        failures = failures + 1 if time.monotonic() - started < 60 else 1
        print(f'workmesh: service exited {code}; failure {failures}/5', file=sys.stderr, flush=True)
        if failures >= 5: break
        until = time.monotonic() + min(2 ** failures, 15)
        while not stopping and time.monotonic() < until: time.sleep(.2)
finally:
    try: os.unlink(record)
    except FileNotFoundError: pass
PY
}

service_control() {
  python_cmd - "$STATE_DIR/services/$1.json" "${2:-status}" "$STATE_DIR/services/$1.sh" <<'PY'
import json, os, signal, subprocess, sys, time
path, action, expected = sys.argv[1:]
try:
    row = json.load(open(path)); pid = int(row['pid'])
    start = subprocess.check_output(['ps', '-p', str(pid), '-o', 'lstart='], text=True, stderr=subprocess.DEVNULL).strip()
    args = subprocess.check_output(['ps', '-p', str(pid), '-o', 'args='], text=True).strip()
    if pid <= 1 or start != row['start'] or row['launcher'] != expected or expected not in args or os.getpgid(pid) != pid:
        raise ValueError('stale pid record')
except (OSError, ValueError, KeyError, subprocess.SubprocessError):
    sys.exit(1)
if action == 'stop':
    os.killpg(pid, signal.SIGTERM)
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        try: os.killpg(pid, 0)
        except ProcessLookupError: break
        time.sleep(.1)
    else:
        # This group was created by our supervisor, not a shared daemon.
        try: os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError: pass
PY
}

start_service() {
  local name=$1 cwd=$2
  shift 2
  if service_control "$name" status; then say "$name already running"; return; fi
  ensure_dirs
  local lock=$STATE_DIR/services/$name.starting
  if ! mkdir "$lock" 2>/dev/null; then die "$name is starting in another process, or has a stale lock at $lock"; fi
  SERVICE_LOCKS+=("$lock")
  if service_control "$name" status; then rmdir "$lock"; SERVICE_LOCKS=(); return; fi
  local launcher=$STATE_DIR/services/$name.sh
  {
    printf '#!/usr/bin/env bash\nset -e\ncd %q\nexec ' "$cwd"
    printf '%q ' "$@"
    printf '\n'
  } > "$launcher"
  chmod 700 "$launcher"
  write_supervisor
  nohup "$(command -v python3)" "$STATE_DIR/services/supervisor.py" "$launcher" "$STATE_DIR/services/$name.json" \
    </dev/null >>"$STATE_DIR/logs/$name.log" 2>&1 &
  local attempt
  for attempt in 1 2 3 4 5; do
    if service_control "$name" status; then
      STARTED_SERVICES+=("$name")
      rmdir "$lock"
      SERVICE_LOCKS=()
      say "Started $name; log: $STATE_DIR/logs/$name.log"
      return
    fi
    sleep .2
  done
  die "$name failed to start; see its log"
}

wait_http() {
  local url=$1 name=$2 attempt
  for attempt in $(seq 1 40); do
    if curl --silent --fail --noproxy '*' --max-time 2 "$url" -o /dev/null; then return; fi
    service_control "$name" status || die "$name exited; see $STATE_DIR/logs/$name.log"
    sleep 1
  done
  die "$name did not become healthy; see $STATE_DIR/logs/$name.log"
}

ts() { if [ -n "$TS_SOCKET" ]; then tailscale --socket="$TS_SOCKET" "$@"; else tailscale "$@"; fi; }
ts_running() { ts status --json 2>/dev/null | python_cmd -c 'import json,sys; sys.exit(0 if json.load(sys.stdin).get("BackendState")=="Running" else 1)' 2>/dev/null; }
start_tailscale() {
  [ "$TS_ENABLED" != no ] || return 0
  have tailscale || die 'Tailscale is not installed; run install first'
  if [ -z "$TS_SOCKET" ] && [ -S "$STATE_DIR/tailscale/tailscaled.sock" ]; then TS_SOCKET=$STATE_DIR/tailscale/tailscaled.sock; fi
  if ts_running; then
    say 'Reusing the authenticated Tailscale daemon'
    return
  fi
  if [ "$TS_MODE" = existing ]; then die 'TS_MODE=existing requires an authenticated Tailscale daemon'; fi
  if [ "$PLATFORM" = darwin ]; then die 'Start and authenticate the system Tailscale app/daemon on macOS first'; fi
  local mode=$TS_MODE
  if [ "$mode" = auto ]; then
    mode=userspace
    if [ "$(id -u)" = 0 ] && [ -c /dev/net/tun ] && python_cmd -c 'import re; s=open("/proc/self/status").read(); raise SystemExit(0 if int(re.search(r"CapEff:\s*(\w+)",s)[1],16)&(1<<12) else 1)'; then mode=kernel; fi
  fi
  [ "$mode" != kernel ] || [ "$(id -u)" = 0 ] || die 'kernel mode needs root; use a preconfigured system daemon or userspace mode'
  TS_SOCKET=${TS_SOCKET:-$STATE_DIR/tailscale/tailscaled.sock}
  mkdir -p "$STATE_DIR/tailscale"
  local args=("$(command -v tailscaled)" "--state=$STATE_DIR/tailscale/tailscaled.state" "--socket=$TS_SOCKET" "--statedir=$STATE_DIR/tailscale")
  if [ "$mode" = userspace ]; then args+=(--tun=userspace-networking "--socks5-server=127.0.0.1:$TS_SOCKS_PORT" "--outbound-http-proxy-listen=127.0.0.1:$TS_HTTP_PORT"); fi
  start_service tailscaled "$WB_ROOT" "${args[@]}"
  local attempt
  for attempt in $(seq 1 30); do [ ! -S "$TS_SOCKET" ] || break; [ "$attempt" -ne 30 ] || die 'tailscaled did not create its socket'; sleep .2; done
  local accept_dns=$TS_ACCEPT_DNS
  if [ "$accept_dns" = auto ]; then
    if [ "$mode" = kernel ]; then accept_dns=true; else accept_dns=false; fi
  fi
  case "$accept_dns" in true|false) ;; *) die 'TS_ACCEPT_DNS must be auto, true or false' ;; esac
  local up=(up "--hostname=$WB_NODE_NAME" "--accept-dns=$accept_dns" --accept-routes=false --timeout=30s)
  [ -z "$TS_TAGS" ] || up+=("--advertise-tags=$TS_TAGS")
  local keyfile=$TS_AUTHKEY_FILE
  if [ -z "$keyfile" ] && [ -n "${TS_AUTHKEY:-}" ]; then temp_dir; keyfile=$TMP_DIR/tailscale.auth; printf '%s' "$TS_AUTHKEY" > "$keyfile"; fi
  [ -z "$keyfile" ] || up+=("--auth-key=file:$keyfile")
  if ! ts "${up[@]}"; then die 'Tailscale login is pending or failed; complete the displayed URL, then run up again'; fi
  ts_running || die 'Tailscale has not reached Running state'
  printf '%s\n' "$mode" > "$STATE_DIR/tailscale/mode"
}

write_forwarder() {
  cat > "$STATE_DIR/services/forward.py" <<'PY'
import socketserver, subprocess, sys, threading
local_port, host, port, binary, sock = sys.argv[1:]
class Bridge(socketserver.BaseRequestHandler):
    def handle(self):
        argv = [binary] + (['--socket=' + sock] if sock else []) + ['nc', host, port]
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        def upload():
            try:
                while True:
                    chunk = self.request.recv(65536)
                    if not chunk: break
                    proc.stdin.write(chunk); proc.stdin.flush()
            except (BrokenPipeError, OSError): pass
            finally:
                try: proc.stdin.close()
                except OSError: pass
        threading.Thread(target=upload, daemon=True).start()
        try:
            while True:
                chunk = proc.stdout.read1(65536)
                if not chunk: break
                self.request.sendall(chunk)
        except OSError: pass
        finally:
            try: self.request.shutdown(2)
            except OSError: pass
            proc.terminate(); proc.wait()
class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
with Server(('127.0.0.1', int(local_port)), Bridge) as server: server.serve_forever()
PY
}
start_forwards() {
  local item local_port target host port
  for item in "${TAILNET_FORWARDS[@]}"; do
    local_port=${item%%=*}; target=${item#*=}; host=${target%:*}; port=${target##*:}
    [[ "$local_port" =~ ^[0-9]+$ && "$port" =~ ^[0-9]+$ && "$host" =~ ^[a-zA-Z0-9._-]+$ ]] || die 'forward format is LOCALPORT=hostname:PORT'
    [ "$TS_ENABLED" != no ] || die 'TAILNET_FORWARDS requires Tailscale'
    write_forwarder
    start_service "forward-$local_port" "$WB_ROOT" "$(command -v python3)" "$STATE_DIR/services/forward.py" "$local_port" "$host" "$port" "$(command -v tailscale)" "$TS_SOCKET"
  done
}

start_cairn() {
  [ "$CAIRN_MODE" != off ] || return 0
  have cairn || die 'Cairn is not installed'
  if [ "$CAIRN_MODE" = node ]; then
    mkdir -p "$STATE_DIR/cairn"
    local bind=$CAIRN_P2P_BIND ip file
    if [ "$bind" = tailnet ]; then
      ip=$(ts ip -4 2>/dev/null | head -1) || true
      # Userspace mode has a tailnet IP but no kernel interface to bind.
      if [ -n "$ip" ] && python_cmd -c 'import socket,sys; s=socket.socket(); s.bind((sys.argv[1],0))' "$ip" 2>/dev/null; then bind=$ip; else bind=127.0.0.1; fi
    fi
    local http_bind=$CAIRN_HTTP_BIND
    if [ "$http_bind" = tailnet ]; then
      http_bind=$(ts ip -4 2>/dev/null | head -1)
      [ -n "$http_bind" ] || die 'CAIRN_HTTP_BIND=tailnet requires a kernel tailnet interface'
      python_cmd -c 'import socket,sys; s=socket.socket(); s.bind((sys.argv[1],0))' "$http_bind" 2>/dev/null || die 'userspace Tailscale cannot bind the tailnet IP; use loopback and tailscale serve or a forward'
    fi
    local args=("$(command -v cairn)" --data-dir "$STATE_DIR/cairn" run --no-mcp \
      --listen "$bind:$CAIRN_P2P_PORT" --serve "$http_bind:$CAIRN_HTTP_PORT")
    for file in "${CAIRN_BOOTSTRAP_FILES[@]}"; do [ -r "$file" ] || die 'Cairn bootstrap file is unreadable'; args+=(--bootstrap "$file"); done
    if [ -n "${CAIRN_BOOTSTRAP_DIR:-}" ]; then
      for file in "$CAIRN_BOOTSTRAP_DIR"/*.json; do [ ! -f "$file" ] || args+=(--bootstrap "$file"); done
    fi
    # This mesh is private. Public seeds, multicast and router port mapping stay off.
    export CAIRN_NETWORK=private CAIRN_REQUIRE_SANDBOX=1 CAIRN_PEERS
    if [ -n "${CAIRN_FLEET_IDENTITY:-}" ]; then export CAIRN_FLEET=enrolled CAIRN_FLEET_IDENTITY; args+=(--mcp-identity "$CAIRN_FLEET_IDENTITY"); fi
    start_service cairn "$WORK_DIR" "${args[@]}"
    [ "$http_bind" != 0.0.0.0 ] || http_bind=127.0.0.1
    wait_http "http://$http_bind:$CAIRN_HTTP_PORT/network" cairn
    CAIRN_NODE_URL=${CAIRN_NODE_URL:-http://$http_bind:$CAIRN_HTTP_PORT}
  else [ -n "${CAIRN_NODE_URL:-}${CAIRN_FLEET_FILE:-}" ] || die 'worker mode needs CAIRN_NODE_URL or CAIRN_FLEET_FILE'; fi
  if [ "$CAIRN_AGENT" = yes ] || { [ "$CAIRN_AGENT" = auto ] && [ "$PLATFORM" = linux ]; }; then
    local agent=("$(command -v cairn)" agent run --data-dir "$STATE_DIR/agent" --name "$WB_NODE_NAME" \
      --roles executor --sandbox "$CAIRN_AGENT_SANDBOX" --parallel "$CAIRN_PARALLEL")
    [ -z "${CAIRN_NODE_URL:-}" ] || agent+=(--node "$CAIRN_NODE_URL")
    [ -z "${CAIRN_FLEET_FILE:-}" ] || agent+=(--fleet "$CAIRN_FLEET_FILE")
    start_service cairn-agent "$WORK_DIR" "${agent[@]}"
  fi
}

start_conductor() {
  [ "$CONDUCTOR_MODE" != off ] || return 0
  have conductor || die 'Conductor is not installed'
  if [ "$CONDUCTOR_MODE" = client ]; then
    [ -n "${CONDUCTOR_ENDPOINT:-}" ] || die 'client mode requires CONDUCTOR_ENDPOINT'
    validate_remote_conductor_endpoint "$CONDUCTOR_ENDPOINT"
    export CONDUCTOR_ENDPOINT
    # Login via an injected token or existing saved CLI credentials. Avoid --token.
    conductor_api status >/dev/null || die 'Conductor client cannot reach/authenticate to the leader; run login or inject CONDUCTOR_TOKEN_FILE'
    conductor_api login --endpoint "$CONDUCTOR_ENDPOINT" --project "$CONDUCTOR_PROJECT"
  elif [ "$CONDUCTOR_MODE" = local ]; then
    # `up` has its own idempotent daemon manager and generates DB credentials.
    # Do not adopt/reconfigure a saved remote endpoint implicitly.
    # Capture whether a daemon existed before `up`; never claim another launcher's.
    local pidfile=$HOME/.conductor/runtime/conductord.pid before_pid=
    [ ! -r "$pidfile" ] || before_pid=$(cat "$pidfile")
    conductor up --endpoint "http://127.0.0.1:$CONDUCTOR_PORT" --addr "127.0.0.1:$CONDUCTOR_PORT" --project "$CONDUCTOR_PROJECT"
    if [ -r "$pidfile" ] && [ "$(cat "$pidfile")" != "$before_pid" ]; then
      python_cmd - "$pidfile" "$STATE_DIR/conductor-owned.json" "$CONDUCTOR_PORT" <<'PY'
import json, subprocess, sys
pid = int(open(sys.argv[1]).read())
stamp = subprocess.check_output(['ps','-p',str(pid),'-o','lstart='],text=True).strip()
args = subprocess.check_output(['ps','-p',str(pid),'-o','args='],text=True).strip()
if 'conductord' not in args or '127.0.0.1:' + sys.argv[3] not in args: raise SystemExit('cannot identify newly started conductord')
with open(sys.argv[2], 'w') as f: json.dump({'pid':pid, 'start':stamp, 'args':args},f)
PY
      NEW_CONDUCTOR=yes
    fi
    CONDUCTOR_ENDPOINT=http://127.0.0.1:$CONDUCTOR_PORT
    export CONDUCTOR_ENDPOINT
  else
    [ -n "${DATABASE_URL:-}" ] || die 'Conductor peer needs DATABASE_URL_FILE or DATABASE_URL'
    [ -r "${CONDUCTOR_PEER_CA:-}" ] && [ -r "${CONDUCTOR_PEER_CERT:-}" ] && [ -r "${CONDUCTOR_PEER_KEY:-}" ] || die 'Conductor peer needs its existing mesh CA, per-node certificate and key'
    [ -n "${CONDUCTOR_PEERS:-}${CONDUCTOR_PEER_DISCOVER_DNS:-}" ] || die 'Conductor peer needs peer URLs or a DNS SRV discovery name'
    export CONDUCTOR_PEER_CA CONDUCTOR_PEER_CERT CONDUCTOR_PEER_KEY CONDUCTOR_PEERS CONDUCTOR_PEER_DISCOVER_DNS
    export CONDUCTOR_PEER_DNS_SERVER
    local addr=${CONDUCTOR_BIND:-127.0.0.1}:$CONDUCTOR_PORT
    start_service conductor "$WORK_DIR" "$(command -v conductord)" --addr "$addr" \
      --peer-ca "$CONDUCTOR_PEER_CA" --peer-cert "$CONDUCTOR_PEER_CERT" --peer-key "$CONDUCTOR_PEER_KEY"
    # Peer CA is also the API trust root; no TLS verification bypass.
    export CONDUCTOR_CA_CERT=$CONDUCTOR_PEER_CA
    CONDUCTOR_ENDPOINT=${CONDUCTOR_ENDPOINT:-https://$WB_NODE_NAME:$CONDUCTOR_PORT}
    validate_remote_conductor_endpoint "$CONDUCTOR_ENDPOINT"
    export CONDUCTOR_ENDPOINT
    conductor_api status >/dev/null || die 'peer started; bootstrap its project/login with existing organization credentials before integrating tools'
    conductor_api login --endpoint "$CONDUCTOR_ENDPOINT" --project "$CONDUCTOR_PROJECT"
  fi
  write_mcp_launcher
  if [ "$CONDUCTOR_INTEGRATE" = yes ]; then
    export CONDUCTOR_PROJECT
    # Explicitly connect Cursor even when only its desktop is on another machine.
    local tool
    for tool in claude codex cursor opencode; do conductor_api integrate "$tool" --global --project "$CONDUCTOR_PROJECT"; done
  fi
}

login_tools() {
  if [ ! -t 0 ]; then say 'Interactive login needs a terminal. Run: bash bootstrap.sh login [--config FILE]'; return; fi
  have claude && { claude auth status >/dev/null 2>&1 || claude auth login; }
  have codex && { codex login status >/dev/null 2>&1 || codex login --device-auth; }
  if have cursor-agent; then cursor-agent status >/dev/null 2>&1 || cursor-agent login
  elif have agent; then say 'For Cursor CLI authentication run: agent login'; fi
  if have opencode; then say 'Choose OpenCode providers with: opencode auth login'; fi
  if [ "$CONDUCTOR_MODE" = client ] && have conductor; then
    say 'If needed, sign in with: conductor login --endpoint URL --sso PROVIDER (or conductor join INVITE)'
  fi
}

start_remote() {
  [ "$CLAUDE_RC" != yes ] || have claude || die 'CLAUDE_RC=yes requires the Claude CLI'
  [ "$CODEX_RC" != yes ] || have codex || die 'CODEX_RC=yes requires the Codex CLI'
  if [ "$CLAUDE_RC" != no ] && have claude; then
    if claude auth status >/dev/null 2>&1; then
      start_service claude-rc "$WORK_DIR" "$(command -v claude)" remote-control
      say "Claude Remote Control link is in $STATE_DIR/logs/claude-rc.log"
    elif [ "$CLAUDE_RC" = yes ]; then die 'Claude Remote Control requires claude auth login'; else say 'Claude Remote Control pending login'; fi
  fi
  if [ "$CODEX_RC" != no ] && have codex; then
    if codex login status >/dev/null 2>&1 && codex remote-control --help >/dev/null 2>&1; then
      codex remote-control start
      printf 'yes\n' > "$STATE_DIR/codex-remote-requested"
    elif [ "$CODEX_RC" = yes ]; then die 'Codex Remote Control requires login and a CLI supporting remote-control'; else say 'Codex Remote Control pending login or supported CLI'; fi
  fi
}

stop_all() {
  local file name files=()
  if [ "${1:-all}" = new ]; then
    for name in "${STARTED_SERVICES[@]}"; do files+=("$STATE_DIR/services/$name.json"); done
  else files=("$STATE_DIR/services"/*.json); fi
  for file in "${files[@]}"; do
    [ -f "$file" ] || continue
    name=$(basename "$file" .json)
    service_control "$name" stop || true
  done
  if [ -f "$STATE_DIR/conductor-owned.json" ] && { [ "${1:-all}" != new ] || [ "$NEW_CONDUCTOR" = yes ]; }; then
    python_cmd - "$STATE_DIR/conductor-owned.json" <<'PY'
import json, os, signal, subprocess, sys
try:
    row=json.load(open(sys.argv[1])); pid=int(row['pid'])
    stamp=subprocess.check_output(['ps','-p',str(pid),'-o','lstart='],text=True,stderr=subprocess.DEVNULL).strip()
    args=subprocess.check_output(['ps','-p',str(pid),'-o','args='],text=True).strip()
    if pid > 1 and stamp == row['start'] and args == row['args'] and os.getpgid(pid) == pid: os.killpg(pid,signal.SIGTERM)
except (OSError,ValueError,KeyError,subprocess.SubprocessError): pass
os.unlink(sys.argv[1])
PY
  fi
  # Codex Remote Control may share the app server with interactive Codex sessions;
  # never stop that shared daemon from this launcher.
}

doctor() {
  local failed=0 tool file
  for tool in python3 cargo rustc go node cmake; do
    if have "$tool"; then say "OK $tool"; else say "MISSING $tool"; failed=1; fi
  done
  if [ "$PROFILE" != minimal ]; then
    for tool in sage gp Singular msolve; do
      if { [ "$tool" = sage ] && [ "$SAGE_MODE" != stock ]; } || have "$tool"; then say "OK $tool ($SAGE_MODE Sage selection)"; else say "MISSING $tool"; failed=1; fi
    done
  fi
  if [ "$TS_ENABLED" != no ]; then
    if have tailscale && ts_running; then say 'OK Tailscale authenticated'; else say 'PENDING Tailscale authentication'; failed=1; fi
  fi
  if [ "$CAIRN_MODE" = node ]; then
    if curl --fail --silent --noproxy '*' --max-time 3 "http://127.0.0.1:$CAIRN_HTTP_PORT/network" >/dev/null; then say 'OK Cairn API'; else say 'MISSING Cairn API'; failed=1; fi
    if [ "${#CAIRN_BOOTSTRAP_FILES[@]}" -eq 0 ] && [ -z "${CAIRN_BOOTSTRAP_DIR:-}" ]; then say 'PENDING Cairn peer bootstrap: node is private and has no configured peers'; failed=1; fi
  fi
  if [ "$CONDUCTOR_MODE" != off ]; then
    if have conductor && conductor_api status >/dev/null; then say 'OK Conductor authenticated'; else say 'PENDING Conductor connectivity/login'; failed=1; fi
  fi
  for file in "$STATE_DIR/services"/*.json; do
    [ -f "$file" ] || continue
    if service_control "$(basename "$file" .json)" status; then say "OK service $(basename "$file" .json)"; else say "STALE service $(basename "$file" .json)"; failed=1; fi
  done
  if [ "$DOCKER_MODE" != off ]; then
    if have docker && docker info >/dev/null 2>&1; then say 'OK Docker engine'; else say 'UNAVAILABLE Docker engine (CLI alone cannot run containers)'; failed=1; fi
  fi
  if have cairn; then cairn agent probe || failed=1; fi
  return "$failed"
}

install_all() {
  ensure_dirs
  install_system
  have curl && have python3 || die 'curl and Python 3 are required'
  PYTHON=$(command -v python3)
  # The bootstrap's metadata parsers require Python >=3.9.
  python_cmd -c 'import sys; raise SystemExit(sys.version_info < (3,9))' || die 'Python 3.9+ is required'
  install_rust
  install_go
  if [ "$PROFILE" = full ]; then
    have cargo-deny || cargo install cargo-deny --locked
    have typst || cargo install typst-cli --locked
    have staticcheck || GOBIN=$BIN_DIR go install honnef.co/go/tools/cmd/staticcheck@latest
    have govulncheck || GOBIN=$BIN_DIR go install golang.org/x/vuln/cmd/govulncheck@latest
  fi
  install_node
  install_science
  install_msolve
  install_cuda
  install_cloud_tools
  install_agent_stack
  install_clis
  install_nodes
  install_tailscale
  install_docker
  install_isolation
  write_environment
  say "Installed. Source: $WB_ROOT/env.sh"
}

up_all() {
  ensure_dirs
  [ -d "$WORK_DIR" ] || die 'working directory does not exist'
  activate_paths
  cd "$WORK_DIR"
  load_secrets
  start_tailscale
  start_forwards
  start_cairn
  start_conductor
  write_environment
}

# Sourcing is useful for integration tests; normal launches execute the dispatch.
if [ "${BASH_SOURCE[0]}" != "$0" ]; then return 0; fi
activate_paths

case "$COMMAND" in
  install) install_all ;;
  bootstrap)
    install_all
    load_secrets
    if [ "$LOGIN" = yes ] || { [ "$LOGIN" = auto ] && [ -t 0 ]; }; then login_tools; fi
    up_all
    start_remote
    say 'Workspace started. Run doctor to check membership and actual runtime capabilities.'
    ;;
  up) up_all; start_remote ;;
  login) load_secrets; login_tools ;;
  remote) ensure_dirs; load_secrets; start_remote ;;
  doctor) load_secrets; [ ! -S "$STATE_DIR/tailscale/tailscaled.sock" ] || TS_SOCKET=$STATE_DIR/tailscale/tailscaled.sock; doctor ;;
  stop) stop_all all ;;
  export-peer)
    cairn seeds publish --identity "$STATE_DIR/cairn/node.identity.json" --out "$STATE_DIR/public-peer"
    ;;
  run)
    [ "${#CHILD[@]}" -gt 0 ] || die 'run requires -- command args...'
    [ "$INSTALL_ON_RUN" != yes ] || install_all
    trap 'stop_all new; cleanup' EXIT
    up_all
    start_remote
    child_pid=
    terminate_child() { [ -z "$child_pid" ] || kill -TERM "$child_pid" 2>/dev/null || true; }
    trap terminate_child TERM INT
    cat > "$STATE_DIR/services/foreground.py" <<'PY'
import os, signal, subprocess, sys
child = subprocess.Popen(sys.argv[1:], start_new_session=True)
def forward(signum, frame):
    try: os.killpg(child.pid, signum)
    except ProcessLookupError: pass
signal.signal(signal.SIGTERM, forward)
signal.signal(signal.SIGINT, forward)
code = child.wait()
sys.exit(code if code >= 0 else 128-code)
PY
    "$(command -v python3)" "$STATE_DIR/services/foreground.py" "${CHILD[@]}" <&0 &
    child_pid=$!
    result=0
    wait "$child_pid" || result=$?
    if kill -0 "$child_pid" 2>/dev/null; then wait "$child_pid" || result=$?; fi
    exit "$result"
    ;;
esac
