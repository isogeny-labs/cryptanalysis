#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/lean"
lake build
lake env lean AxiomAudit.lean
lake env lean --run .lake/packages/CryptoLean/tools/AuditAxioms.lean Retrospective.RhoCollision
