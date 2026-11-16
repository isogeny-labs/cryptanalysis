#!/usr/bin/env bash
# Exact published source/file preparation only; no AWS/checkpoint/science.
# --verify-existing uses read-only Git/file checks on a completed runtime.
set -euo pipefail
if [[ ${1:-} == --copy-consumer-files ]];then
 [[ $# == 5 ]] || exit 2
 expanded=$2;runtime=$3;list=$4;tracked=$5;repo=$runtime/cryptanalysis
 while IFS= read -r relative;do
  input=$expanded/cryptanalysis/$relative
  target=$repo/$relative
  resolved=0
  for depth in {1..32};do
   [[ $target == "$repo/"* || $target == "$runtime/crypto/"* ]]
   [[ $target != "$repo/.git" && $target != "$repo/.git/"* ]]
   if [[ -L $target ]];then target=$(realpath -m "$target");continue;fi
   if [[ ! -e $target && $target == "$repo/"* ]];then
    rel=${target#"$repo/"}
    entry=$(git -C "$repo" ls-files --stage -- "$rel")
    if [[ -n $entry ]];then
     read -r mode oid rest <<< "$entry"
     if [[ $mode == 120000 ]];then
      git -C "$repo" checkout --ignore-skip-worktree-bits HEAD -- "$rel"
      continue
     fi
     [[ $mode == 100644 || $mode == 100755 ]]
     [[ $(git -C "$repo" hash-object --no-filters "$input") == "$oid" ]]
     printf '%s\n' "$rel" >> "$tracked"
    fi
   fi
   resolved=1
   break
  done
  [[ $resolved == 1 && ! -L $target && $target == "$runtime/"* ]]
  if [[ -e $target ]];then
   [[ -f $target ]]
   cmp "$input" "$target"
  else
   mkdir -p "$(dirname -- "$target")"
   ln "$input" "$target"
  fi
  printf '%s\t%s\n' "$relative" "${target#"$runtime/"}"
 done < "$list"
 exit 0
fi
verify_existing=0
if [[ ${1:-} == --verify-existing ]];then verify_existing=1;shift;fi
if [[ $verify_existing == 1 ]];then [[ $# == 4 || $# == 5 ]] || exit 2;else [[ $# == 3 || $# == 4 ]] || exit 2;fi
snapshot=$(realpath -e "$1")
expected=$2
out=$(realpath -m "$3")
[[ $expected == 2c44ee2ebb0be9b5fc0375818cc18924cef82c41 && ! -e $out && ! -L $out ]]
expanded_argument=''
if [[ $verify_existing == 1 ]];then
 runtime=$(realpath -e "$4")
 [[ $runtime != "$out" && $out != "$runtime/"* && -d $runtime/cryptanalysis/.git ]]
 expanded_argument=${5:-}
else
 runtime=$out/runtime
 expanded_argument=${4:-}
fi
export GIT_OPTIONAL_LOCKS=0
mkdir "$out"
cp "$0" "$out/entire-actual-source-preparation.sh"
date -u +%FT%TZ > "$out/start.txt"
current_pid=''
finish(){
 local code=$?
 trap - EXIT TERM INT
 set +e
 if [[ -n $current_pid ]];then kill -TERM "$current_pid" 2>/dev/null;wait "$current_pid";fi
 printf '%s\n' "$code" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 exit "$code"
}
trap finish EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
phase(){
 local name=$1 cap=120 now left code;shift
 if [[ -n ${LP_ABSOLUTE_DEADLINE_EPOCH:-} || -n ${LP_ATTEMPT_STARTED_EPOCH:-} ]];then
  [[ ${LP_ATTEMPT_STARTED_EPOCH:-} =~ ^[1-9][0-9]{9}$ && ${LP_ABSOLUTE_DEADLINE_EPOCH:-} =~ ^[1-9][0-9]{9}$ ]]
  (( LP_ABSOLUTE_DEADLINE_EPOCH > LP_ATTEMPT_STARTED_EPOCH && LP_ABSOLUTE_DEADLINE_EPOCH <= LP_ATTEMPT_STARTED_EPOCH+3600 ))
  now=$(date -u +%s);left=$((LP_ABSOLUTE_DEADLINE_EPOCH-now-60))
  (( now >= LP_ATTEMPT_STARTED_EPOCH && left > 0 )) || return 125
  (( left >= cap )) || cap=$left
 fi
 jq --null-input --args '$ARGS.positional' -- "$@" > "$out/$name.argv.json"
 set +e
 (ulimit -v 2097152;exec timeout --signal=TERM --kill-after=5s "$cap" "$@") > "$out/$name.stdout" 2> "$out/$name.stderr" &
 current_pid=$!;wait "$current_pid";code=$?;current_pid=''
 set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s\n' "$name" "$code" >> "$out/all-actual-source-preparation-phases.txt"
 return "$code"
}
[[ -f $snapshot && ! -L $snapshot && $(wc -c < "$snapshot") == 39331840 ]]
printf '%s  %s\n' b441b4375616df79da9b879dd3d1fc04b8f31ae81b0d2c68c98833c3077fb7b8 "$snapshot" > "$out/original-whole-snapshot.sha256"
phase initial-whole-snapshot-bytes sha256sum --check "$out/original-whole-snapshot.sha256"
if [[ $verify_existing == 0 ]];then mkdir "$runtime";fi
phase whole-snapshot-member-list tar --list --file "$snapshot"
if [[ -n $expanded_argument ]];then
 expanded=$(realpath -e "$expanded_argument")
 [[ $out != "$expanded" && $out != "$expanded/"* ]]
else
 expanded=$out/entire-snapshot-files
 mkdir "$expanded"
 phase materialize-entire-snapshot tar --extract --file "$snapshot" --directory "$expanded"
fi
phase compare-entire-snapshot tar --compare --file "$snapshot" --directory "$expanded"
consumer_files=0
all_files=0
: > "$out/entire-consumer-snapshot-files.txt"
printf '%s\n' '**/.gitignore' '**/.gitattributes' '**/.artifacts.json' > "$out/entire-source-sparse-patterns-unsorted.txt"
for extra in .gitignore .gitattributes .resume/RESUME.md scripts/checkpoint.sh docs/chained-transfer-checkpoint-transport/PROTOCOL_01.md;do
 printf '/%s\n' "$extra" >> "$out/entire-source-sparse-patterns-unsorted.txt"
done
while IFS= read -r member;do
 [[ $member == crypto/* || $member == cryptanalysis/* ]]
 [[ $member != /* && $member != *'/../'* && $member != *'\\'* && $member != *'*'* && $member != *'?'* && $member != *'['* && $member != *'!'* && $member != *' '* ]]
 [[ $member != */ ]] || continue
 [[ -f $expanded/$member && ! -L $expanded/$member ]]
 all_files=$((all_files+1))
 [[ $member == cryptanalysis/* ]] || continue
 relative=${member#cryptanalysis/}
 printf '%s\n' "$relative" >> "$out/entire-consumer-snapshot-files.txt"
 printf '/%s\n' "$relative" >> "$out/entire-source-sparse-patterns-unsorted.txt"
 consumer_files=$((consumer_files+1))
 parent=.
 [[ $relative != */* ]] || parent=${relative%/*}
 while :;do
  for metadata in .gitignore .gitattributes .artifacts.json;do
   if [[ $parent == . ]];then printf '/%s\n' "$metadata";else printf '/%s/%s\n' "$parent" "$metadata";fi
  done >> "$out/entire-source-sparse-patterns-unsorted.txt"
  [[ $parent != . ]] || break
  if [[ $parent == */* ]];then parent=${parent%/*};else parent=.;fi
 done
done < "$out/whole-snapshot-member-list.stdout"
[[ $all_files == 1663 && $consumer_files == 1310 ]]
LC_ALL=C sort --unique "$out/entire-source-sparse-patterns-unsorted.txt" > "$out/entire-source-sparse-patterns.txt"
repo=$runtime/cryptanalysis
source_branch=research/chained-transfer-lp-presentation-20261115
remote_ref=refs/remotes/origin/$source_branch
if [[ $verify_existing == 0 ]];then
phase initialize-fresh-public-repository git init --quiet "$repo"
phase public-source-origin git -C "$repo" remote add origin https://github.com/isogeny-labs/cryptanalysis.git
phase enable-exact-file-sparse-checkout git -C "$repo" config core.sparseCheckout true
phase configure-exact-file-sparse-checkout git -C "$repo" config core.sparseCheckoutCone false
mkdir -p "$repo/.git/info"
cp "$out/entire-source-sparse-patterns.txt" "$repo/.git/info/sparse-checkout"
phase observe-real-published-source-branch git ls-remote --heads https://github.com/isogeny-labs/cryptanalysis.git "refs/heads/$source_branch"
read -r observed advertised < "$out/observe-real-published-source-branch.stdout"
[[ $observed =~ ^[a-f0-9]{40}$ && $advertised == "refs/heads/$source_branch" ]]
# Fetch a real advertised branch; never fabricate a remote tracking reference
# merely to suppress the unchanged checkpoint's unpushed-commit detection.
phase fetch-real-published-source-branch git -C "$repo" fetch --no-tags --filter=blob:none --depth=64 origin "refs/heads/$source_branch:$remote_ref"
phase record-actual-fetched-source-head git -C "$repo" rev-parse "$remote_ref"
[[ $(cat "$out/record-actual-fetched-source-head.stdout") == "$observed" ]]
phase require-native-source-ancestor git -C "$repo" merge-base --is-ancestor "$expected" "$remote_ref"
phase checkout-exact-native-source git -C "$repo" checkout --detach "$expected"
phase record-exact-native-source git -C "$repo" rev-parse HEAD
[[ $(cat "$out/record-exact-native-source.stdout") == "$expected" ]]
# Root bytes have the separately recorded44a origin. They are deliberately not
# represented as an actual Root Git checkout or as the original baseline3d.
phase materialize-whole-guarded-Root-bytes cp --archive --link "$expanded/crypto" "$runtime/crypto"
: > "$out/entire-canonical-tracked-data-targets.txt"
phase materialize-all-whole-Consumer-bytes bash "$out/entire-actual-source-preparation.sh" --copy-consumer-files "$expanded" "$runtime" "$out/entire-consumer-snapshot-files.txt" "$out/entire-canonical-tracked-data-targets.txt"
phase canonical-targets-in-real-status bash -c 'cd "$1" && exec git update-index --no-skip-worktree --stdin < "$2"' _ "$repo" "$out/entire-canonical-tracked-data-targets.txt"
else
 phase record-existing-native-source git -C "$repo" rev-parse HEAD
 [[ $(cat "$out/record-existing-native-source.stdout") == "$expected" ]]
 phase record-existing-public-origin git -C "$repo" remote get-url origin
 [[ $(cat "$out/record-existing-public-origin.stdout") == https://github.com/isogeny-labs/cryptanalysis.git ]]
 phase require-existing-real-native-source-ancestor git -C "$repo" merge-base --is-ancestor "$expected" "$remote_ref"
fi
phase compare-every-whole-runtime-source bash -euo pipefail -c '
 expanded=$1;runtime=$2;list=$3;count=0
 while IFS= read -r member;do
  [[ $member != */ ]] || continue
  target=$runtime/$member
  canonical=$(realpath -e "$target")
  [[ $canonical == "$runtime/cryptanalysis/"* || $canonical == "$runtime/crypto/"* ]]
  [[ $canonical != "$runtime/cryptanalysis/.git" && $canonical != "$runtime/cryptanalysis/.git/"* ]]
  [[ -f $canonical && ! -L $canonical ]]
  cmp "$expanded/$member" "$canonical"
  printf "%s\t%s\n" "$member" "${canonical#"$runtime/"}"
  count=$((count+1))
 done < "$list"
 [[ $count == 1663 ]]
' _ "$expanded" "$runtime" "$out/whole-snapshot-member-list.stdout"
phase all-original1605-source-bytes bash -c 'cd "$1" && exec sha256sum --check experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256' _ "$repo"
phase all-pure50-source-bytes bash -c 'cd "$1" && exec sha256sum --check experiments/chained-transfer-lp-presentation-01/historical-01/source-01.sha256' _ "$repo"
phase all-population12-source-bytes bash -c 'cd "$1" && exec sha256sum --check experiments/chained-transfer-lp-presentation-01/population-01/source-01.sha256' _ "$repo"
phase actual-clean-source-status env GIT_OPTIONAL_LOCKS=0 git -C "$repo" status --porcelain --untracked-files=all
[[ ! -s $out/actual-clean-source-status.stdout ]]
phase original-unpushed-commit-count git -C "$repo" rev-list --count HEAD --not --remotes
[[ $(cat "$out/original-unpushed-commit-count.stdout") == 0 ]]
phase exact-committed-RESUME git -C "$repo" show HEAD:.resume/RESUME.md
phase entire-committed-RESUME-equality cmp "$repo/.resume/RESUME.md" "$out/exact-committed-RESUME.stdout"
phase final-whole-snapshot-bytes sha256sum --check "$out/original-whole-snapshot.sha256"
printf '%s\n' "$verify_existing" > "$out/verify-existing-mode.txt"
printf '%s\n' 'Fresh mode fetches a real public branch; verify-existing mode performs read-only checks without a new fetch/materialization. Exact native-source2c Git checkout plus exact353 Root dependency files of44a snapshot origin; committed RESUME/source guards verified by original tools. Root is a byte bundle, not a Git checkout. No checkpoint/AWS/native science/image/ABI/admission/EKS qualification; caller must preserve the original absolute deadline and run the unchanged gate/readbacks before scientific execution.' > "$out/scope.txt"
