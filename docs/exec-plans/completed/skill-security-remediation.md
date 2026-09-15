# Plan: Skill security remediation

**Goal**: Remove high-risk installation guidance and establish explicit safety boundaries for untrusted knowledge sources.
**Status**: done
**Started**: 2026-09-15
**Completed**: 2026-09-15

## Steps

- [x] Remove the remote shell-installer command from `kp-init`.
- [x] Define safe remote-source ingestion behavior in `kp-source`.
- [x] Define untrusted-content and bounded-parser behavior in `kp-staging`.
- [x] Define untrusted-content behavior in `kp-wiki`.
- [x] Add automated checks for dangerous shell-install patterns.

## Progress log

- 2026-09-15: Began remediation based on public skills.sh audit findings.
- 2026-09-15: Completed five scoped security commits and validated the policy checker.

## Decision log

- 2026-09-15: Keep all skills functional while replacing implicit trust with explicit boundaries, rather than removing URL and document support.
