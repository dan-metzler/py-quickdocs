---
logo: images/logo.svg
title: Q2 Security Review
subtitle: Infrastructure & Access Control Assessment
revision: Draft 1.2
date: April 2026
color: #1b3a5c
stripe: true
columns: true
---

# Q2 Security Review

This report summarises findings from the Q2 infrastructure and access control assessment conducted across all production environments. Findings are ranked by severity and accompanied by recommended remediation steps.

:::danger
Three critical findings require immediate remediation before the next production release. Do not defer these items.
:::

## Executive Summary

The assessment covered 14 systems across four environment tiers. Overall security posture has improved since Q1, with 8 of 11 previously flagged issues resolved. Three new critical findings were identified.

| Severity | Open | Resolved | Total |
|----------|------|----------|-------|
| Critical | 3    | 1        | 4     |
| High     | 5    | 6        | 11    |
| Medium   | 9    | 12       | 21    |
| Low      | 14   | 22       | 36    |

## Critical Findings

### CF-01 - Exposed Admin Credentials in CI Pipeline

Plaintext AWS credentials were found committed in the `.github/workflows/deploy.yml` file. The credentials have active permissions on the production S3 bucket.

**Affected systems:** `prod-deploy`, `staging-deploy`

**Remediation:**

1. Rotate the exposed credentials immediately
   :::danger
   Do not simply delete the commit - credentials remain in git history. Rotate first, then scrub history.
   :::
2. Move all secrets to GitHub Actions encrypted secrets
3. Add a pre-commit hook to block credential patterns
4. Audit access logs for the exposed key from the past 90 days

### CF-02 - Unencrypted Data at Rest on `db-backup-03`

The backup volume on `db-backup-03` is not encrypted. Backups contain full customer PII snapshots.

**Remediation:**

1. Enable volume encryption immediately - this requires a snapshot and restore cycle
   :::warning
   The restore cycle requires approximately 4 hours of downtime on the backup system. Schedule a maintenance window.
   :::
2. Verify encryption on all other backup volumes
3. Update the infrastructure checklist to include encryption verification

### CF-03 - SSH Root Login Enabled on `gateway-01`

Root SSH login is enabled on the edge gateway. Combined with password authentication (also enabled), this is a high-priority exposure.

```bash
# Verify current state
sshd -T | grep -E "permitrootlogin|passwordauthentication"

# Expected (safe) output:
# permitrootlogin no
# passwordauthentication no
```

:::warning
Disabling password authentication will immediately lock out any users who have not yet configured SSH keys. Audit active sessions before applying.
:::

## High Findings

### HF-01 - Missing MFA on 6 Admin Accounts

Six administrator accounts have MFA disabled. Policy requires MFA for all accounts with elevated privileges.

**Affected accounts:** `ops-alice`, `ops-bob`, `dev-carlos`, `dev-diana`, `svc-deploy`, `svc-monitoring`

:::note!
Service accounts (`svc-*`) require hardware token MFA - TOTP apps are not permitted for service account access.
:::

### HF-02 - Outdated TLS Configuration on Internal APIs

Four internal API services accept TLS 1.0 and 1.1 connections. Only TLS 1.2+ should be accepted.

| Service         | TLS 1.0 | TLS 1.1 | TLS 1.2 | TLS 1.3 |
|----------------|---------|---------|---------|---------|
| `auth-svc`     | ✓       | ✓       | ✓       | ✓       |
| `billing-svc`  | ✓       | ✓       | ✓       | ✗       |
| `notify-svc`   | ✓       | ✓       | ✓       | ✗       |
| `reporting-svc`| ✗       | ✗       | ✓       | ✓       |

:::tip
Use `nmap --script ssl-enum-ciphers -p 443 <host>` to verify TLS configuration before and after remediation.
:::

## Resolved Since Q1

The following previously reported items have been confirmed resolved:

- **HF-Q1-03** - Rate limiting added to authentication endpoints
- **HF-Q1-05** - Container image scanning integrated into CI pipeline
- **MF-Q1-08** - Log retention policy extended to 365 days
- **MF-Q1-11** - Dependency audit automation enabled on all repositories

:::info
Full resolution evidence is available in the Q1 remediation tracker. Contact the security team for access.
:::

---

## Next Review

The follow-up assessment is scheduled for **July 2026**. All critical and high findings must be resolved and verified before that date.
