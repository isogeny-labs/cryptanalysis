#!/usr/bin/env bash
# Read-only diagnostics with the already configured caller. No admission or
# cloud build/job submission is implemented here; lane reservations are unknown.
set -uo pipefail
[[ $# == 2 ]] || exit 2
out=$(realpath -m "$1")
pool_check=$(realpath "$2")
[[ ! -e $out && -f $pool_check ]] || exit 2
mkdir "$out"
cp "$0" "$out/actual-command.sh"
cp "$pool_check" "$out/unchanged-original-pool-check.sh"
date -u +%FT%TZ > "$out/start.txt"
phase() {
 local name=$1 code;shift
 "$@" > "$out/$name.stdout" 2> "$out/$name.stderr"
 code=$?
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s\n' "$name" "$code" >> "$out/all-read-only-phases.txt"
 return "$code"
}
finish() {
 local identity=false budgets=false capacity=false
 [[ -f $out/account-matched ]] && identity=true
 if [[ -f $out/budget-isolab-daily-cost-100.exit && -f $out/budget-spot-experiments-daily-25.exit && -f $out/budget-isolab-monthly-account-cost.exit ]] \
  && [[ $(cat "$out/budget-isolab-daily-cost-100.exit") == 0 && $(cat "$out/budget-spot-experiments-daily-25.exit") == 0 && $(cat "$out/budget-isolab-monthly-account-cost.exit") == 0 ]];then budgets=true;fi
 [[ -f $out/pool-check.exit && $(cat "$out/pool-check.exit") == 0 ]] && capacity=true
 jq --null-input --argjson identity "$identity" --argjson budgets "$budgets" --argjson capacity "$capacity" \
  '{schema:"LP-read-only-admission-diagnostic/v1",existing_identity_matches_lab_account:$identity,
    all_three_original_budget_API_reads_succeeded:$budgets,original_all_tenant_pool_check_fits:$capacity,
    lane_charged_and_reserved_accounting:"unknown",admitted:false,cloud_build_or_job_submitted:false,
    scope:"read-only availability diagnostic; raw commands/exits retained, no new identity or permission"}' > "$out/diagnostic-only-no-admission.json"
 date -u +%FT%TZ > "$out/finish.txt"
}
trap finish EXIT
command -v aws >/dev/null || { printf '127\n' > "$out/AWS-CLI-unavailable.exit";exit 0; }
if ! phase actual-caller timeout 60 aws --region us-east-2 --cli-connect-timeout 10 --cli-read-timeout 20 sts get-caller-identity --output json;then exit 0;fi
if ! jq --exit-status '.Account=="104186811093"' "$out/actual-caller.stdout" > "$out/account-check.stdout" 2> "$out/account-check.stderr";then
 printf '1\n' > "$out/account-check.exit";exit 0
fi
printf '0\n' > "$out/account-check.exit"
: > "$out/account-matched"
for name in isolab-daily-cost-100 spot-experiments-daily-25 isolab-monthly-account-cost;do
 phase "budget-$name" timeout 60 aws --region us-east-1 --cli-connect-timeout 10 --cli-read-timeout 20 \
  budgets describe-budget --account-id 104186811093 --budget-name "$name" --output json || true
done
if ! phase actual-cluster timeout 60 aws --region us-east-2 --cli-connect-timeout 10 --cli-read-timeout 20 \
 eks describe-cluster --name isolab --query 'cluster.{name:name,status:status,version:version,endpoint:endpoint}' --output json;then exit 0;fi
command -v kubectl >/dev/null || { printf '127\n' > "$out/kubectl-unavailable.exit";exit 0; }
export KUBECONFIG=$out/actual-caller-kubeconfig
phase actual-caller-kubeconfig timeout 60 aws --region us-east-2 --cli-connect-timeout 10 --cli-read-timeout 20 \
 eks update-kubeconfig --name isolab --kubeconfig "$KUBECONFIG" || exit 0
# Retain every full/partial response even if the unchanged original helper
# cleans up its own temporary files. The wrapper permits only read operations.
export LP_ADMISSION_ACTUAL_KUBECTL
LP_ADMISSION_ACTUAL_KUBECTL=$(command -v kubectl)
export LP_ADMISSION_CAPTURE=$out/all-entire-pool-read-responses
mkdir "$LP_ADMISSION_CAPTURE" "$out/read-only-command-bin"
cat > "$out/read-only-command-bin/kubectl" <<'EOF'
#!/usr/bin/env bash
[[ ${1:-} == get ]] || exit 2
case ${2:-} in nodepool.karpenter.sh|nodes|pods|resourcequota) ;; *) exit 2;; esac
case_dir=$(mktemp -d "$LP_ADMISSION_CAPTURE/call.XXXXXXXX") || exit 3
printf '%s\0' "$@" > "$case_dir/entire-argv.paths0"
"$LP_ADMISSION_ACTUAL_KUBECTL" "$@" > "$case_dir/entire.stdout" 2> "$case_dir/entire.stderr"
code=$?
printf '%s\n' "$code" > "$case_dir/actual.exit"
cat "$case_dir/entire.stdout"
cat "$case_dir/entire.stderr" >&2
exit "$code"
EOF
chmod +x "$out/read-only-command-bin/kubectl"
export PATH=$out/read-only-command-bin:$PATH
phase pool-check timeout 60 bash "$pool_check" --cpu 2 --memory 4Gi --pool cpu-spot --save "$out/entire-original-pool-bundle.json" --json || true
exit 0
