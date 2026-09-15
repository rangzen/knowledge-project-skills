# Plan: Skill security remediation

**Goal**: Remove high-risk installation guidance and establish explicit safety boundaries for untrusted knowledge sources.
**Status**: in-progress
**Started**: 2026-09-15
**Completed**: —

## Steps

- [ ] Remove the remote shell-installer command from `kp-init`.
- [ ] Define safe remote-source ingestion behavior in `kp-source`.
- [ ] Define untrusted-content and bounded-parser behavior in `kp-staging`.
- [ ] Define untrusted-content behavior in `kp-wiki`.
- [ ] Add automated checks for dangerous shell-install patterns.

## Progress log

- 2026-09-15: Began remediation based on public skills.sh audit findings.

## Decision log

- 2026-09-15: Keep all skills functional while replacing implicit trust with explicit boundaries, rather than removing URL and document support.
