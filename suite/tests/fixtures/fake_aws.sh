#!/usr/bin/env bash
# Stub of the `aws` CLI for the fbkit store tests. Implements exactly:
#   aws s3 cp <src> <dst> [--only-show-errors] [--metadata k=v,...]   (both directions)
#   aws s3api head-object --bucket B --key K [--output json]
#   aws s3api list-objects-v2 --bucket B --prefix P [--no-paginate]
#                             [--continuation-token T] [--output json]
#   aws sts get-caller-identity [--output json]
# Objects live in $FAKE_AWS_ROOT/<bucket>/<key>; user metadata in the sidecar
# <key>.meta.json. Knobs: FAKE_AWS_NO_CREDENTIALS=1 (sts fails like the real
# CLI), FAKE_AWS_PAGE_SIZE (list page size, default 1000), FAKE_AWS_LOG (file
# that receives one line per invocation: the subcommand and its arguments).
set -u
root="${FAKE_AWS_ROOT:-}"
if [ -z "$root" ]; then
  echo "fake_aws: FAKE_AWS_ROOT is not set" >&2
  exit 2
fi
if [ -n "${FAKE_AWS_LOG:-}" ]; then
  printf '%s\n' "$*" >> "$FAKE_AWS_LOG"
fi

json_escape() { local s=${1//\\/\\\\}; printf '%s' "${s//\"/\\\"}"; }

split_s3() { # s3://bucket/key -> BUCKET, KEY
  local rest=${1#s3://}
  BUCKET=${rest%%/*}
  KEY=${rest#*/}
  [ "$KEY" = "$rest" ] && KEY=""
}

not_found() {
  echo "An error occurred (404) when calling the HeadObject operation: Not Found" >&2
  exit 254
}

group="${1:-} ${2:-}"
shift 2 2>/dev/null || true

case "$group" in
"s3 cp")
  src="" dst="" meta=""
  while [ $# -gt 0 ]; do
    case "$1" in
    --only-show-errors) shift ;;
    --metadata) meta="$2"; shift 2 ;;
    *) if [ -z "$src" ]; then src="$1"; else dst="$1"; fi; shift ;;
    esac
  done
  if [[ "$src" == s3://* && "$dst" != s3://* ]]; then
    split_s3 "$src"
    obj="$root/$BUCKET/$KEY"
    if [ ! -f "$obj" ]; then
      echo "download failed: $src to $dst An error occurred (404) when calling the HeadObject operation: Key \"$KEY\" does not exist" >&2
      exit 1
    fi
    cp "$obj" "$dst" || exit 1
  elif [[ "$src" != s3://* && "$dst" == s3://* ]]; then
    split_s3 "$dst"
    obj="$root/$BUCKET/$KEY"
    if [ ! -f "$src" ]; then
      echo "The user-provided path $src does not exist." >&2
      exit 255
    fi
    mkdir -p "$(dirname "$obj")" && cp "$src" "$obj" || exit 1
    out="{\"Metadata\": {"
    first=1
    IFS=',' read -ra kvs <<< "$meta"
    for kv in "${kvs[@]}"; do
      [ -z "$kv" ] && continue
      k=${kv%%=*}; v=${kv#*=}
      [ $first -eq 0 ] && out+=", "
      out+="\"$(json_escape "$k")\": \"$(json_escape "$v")\""
      first=0
    done
    out+="}}"
    printf '%s\n' "$out" > "$obj.meta.json"
  else
    echo "fake_aws: unsupported s3 cp direction" >&2
    exit 2
  fi
  ;;
"s3api head-object")
  bucket="" key=""
  while [ $# -gt 0 ]; do
    case "$1" in
    --bucket) bucket="$2"; shift 2 ;;
    --key) key="$2"; shift 2 ;;
    --output) shift 2 ;;
    *) shift ;;
    esac
  done
  obj="$root/$bucket/$key"
  [ -f "$obj" ] || not_found
  size=$(stat -c %s "$obj")
  etag=$(md5sum "$obj" | cut -d' ' -f1)
  lm=$(date -u -r "$obj" +"%Y-%m-%dT%H:%M:%S+00:00")
  meta='{}'
  if [ -f "$obj.meta.json" ]; then
    meta=$(sed -e 's/^{"Metadata": *//' -e 's/}$//' "$obj.meta.json")
  fi
  printf '{\n    "AcceptRanges": "bytes",\n    "LastModified": "%s",\n    "ContentLength": %s,\n    "ETag": "\\"%s\\"",\n    "ContentType": "binary/octet-stream",\n    "Metadata": %s\n}\n' \
    "$lm" "$size" "$etag" "$meta"
  ;;
"s3api list-objects-v2")
  bucket="" prefix="" token=""
  while [ $# -gt 0 ]; do
    case "$1" in
    --bucket) bucket="$2"; shift 2 ;;
    --prefix) prefix="$2"; shift 2 ;;
    --continuation-token) token="$2"; shift 2 ;;
    --output) shift 2 ;;
    --no-paginate) shift ;;
    *) shift ;;
    esac
  done
  page=${FAKE_AWS_PAGE_SIZE:-1000}
  dir="$root/$bucket"
  keys=()
  if [ -d "$dir" ]; then
    while IFS= read -r f; do
      k=${f#"$dir"/}
      [[ "$k" == "$prefix"* ]] && keys+=("$k")
    done < <(cd "$dir" && find . -type f ! -name '*.meta.json' | sed 's|^\./||' | LC_ALL=C sort | sed "s|^|$dir/|")
  fi
  total=${#keys[@]}
  start=0
  [ -n "$token" ] && start=$token
  end=$((start + page))
  [ $end -gt $total ] && end=$total
  if [ "$total" -eq 0 ]; then
    printf '{\n    "RequestCharged": null\n}\n'
    exit 0
  fi
  printf '{\n    "Contents": ['
  sep=""
  for ((i = start; i < end; i++)); do
    k=${keys[$i]}
    obj="$dir/$k"
    printf '%s\n        {"Key": "%s", "LastModified": "%s", "ETag": "\\"%s\\"", "Size": %s, "StorageClass": "STANDARD"}' \
      "$sep" "$(json_escape "$k")" "$(date -u -r "$obj" +"%Y-%m-%dT%H:%M:%S+00:00")" \
      "$(md5sum "$obj" | cut -d' ' -f1)" "$(stat -c %s "$obj")"
    sep=","
  done
  printf '\n    ]'
  if [ $end -lt $total ]; then
    printf ',\n    "IsTruncated": true,\n    "NextContinuationToken": "%s"' "$end"
  else
    printf ',\n    "IsTruncated": false'
  fi
  printf '\n}\n'
  ;;
"sts get-caller-identity")
  if [ "${FAKE_AWS_NO_CREDENTIALS:-}" = "1" ]; then
    echo 'Unable to locate credentials. You can configure credentials by running "aws configure".' >&2
    exit 253
  fi
  printf '{\n    "UserId": "AIDAFAKEFAKEFAKEFAKE",\n    "Account": "000000000000",\n    "Arn": "arn:aws:iam::000000000000:user/fake"\n}\n'
  ;;
*)
  echo "fake_aws: unsupported command: $group" >&2
  exit 2
  ;;
esac
