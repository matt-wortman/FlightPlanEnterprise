# Legacy ID Mapping Plan (v2 → Enterprise)

**Last Updated:** January 2, 2026  
**Scope:** FlightPlan v2 legacy SQL Server → Enterprise event store

This plan defines how legacy identifiers (MRN, ADM, usernames, row IDs) map to enterprise UUIDs **without exposing PHI**.

---

## Objectives

- Preserve the ability to link every legacy record to its enterprise equivalent.
- Avoid exposing MRNs or other PHI in URLs, logs, or API responses.
- Provide a deterministic way to re-import data without creating duplicates.
- Support future migration to secure identity providers and key management.

---

## Mapping Principles

1. **MRN never stored in plain text** in the event store or logs.  
2. **Opaque UUIDs** are used everywhere in APIs and URLs.  
3. **Deterministic mapping** ensures repeatable imports.  
4. **Mapping tables are tenant-scoped** (multi-tenant safe).

---

## Recommended Mapping Tables (Enterprise DB)

### 1) `patient_identity_map`
| Column | Type | Purpose |
|---|---|---|
| `tenant_id` | UUID | Tenant isolation |
| `patient_id` | UUID | Enterprise patient UUID |
| `mrn_token` | TEXT | Tokenized MRN (HMAC or encrypted) |
| `mrn_ciphertext` | TEXT | Optional encrypted MRN for reversible lookup |
| `created_at` | TIMESTAMP | Audit timestamp |

**Notes:**  
- `mrn_token` is used for deterministic matching and safe lookups.  
- `mrn_ciphertext` is optional and must use KMS-managed keys.  

---

### 2) `admission_identity_map`
| Column | Type | Purpose |
|---|---|---|
| `tenant_id` | UUID | Tenant isolation |
| `admission_id` | UUID | Enterprise admission UUID |
| `legacy_adm_token` | TEXT | Tokenized legacy ADM (HMAC on MRN+ADM) |
| `created_at` | TIMESTAMP | Audit timestamp |

---

### 3) `user_identity_map`
| Column | Type | Purpose |
|---|---|---|
| `tenant_id` | UUID | Tenant isolation |
| `user_id` | UUID | Enterprise user UUID |
| `legacy_username_token` | TEXT | Tokenized legacy username |
| `created_at` | TIMESTAMP | Audit timestamp |

**Notes:**  
- Once Azure AD is in place, map legacy usernames to real identity provider IDs.  

---

## Tokenization Strategy (PHI-Safe)

Use a **keyed HMAC** to produce deterministic, non-reversible tokens:

- `mrn_token = HMAC(key, "MRN:<mrn>")`
- `legacy_adm_token = HMAC(key, "ADM:<mrn>|<adm>")`
- `legacy_username_token = HMAC(key, "USER:<username>")`

**Key management:**  
- Store the HMAC key in a secure secret manager (Azure Key Vault).  
- Rotate keys with a controlled re-tokenization plan.

---

## Import Workflow (High-Level)

1. **Initialize mapping tables** for the tenant.  
2. **Generate deterministic UUIDs** for MRN/ADM if mapping is missing.  
3. **Store mapping records** before event import begins.  
4. **Replay legacy rows** into the event store using those UUIDs.  
5. **Lock mappings** after import to prevent accidental drift.

---

## Validation Checklist

- [ ] No MRN appears in event payloads (only tokens/ciphertext).  
- [ ] Re-running import produces identical UUIDs.  
- [ ] Mapping tables are tenant-isolated.  
- [ ] Audit logs show import timestamps and sources.  
- [ ] Clinician review confirms correct patient/admission alignment.

---

## Related Docs

- `docs/data-model/LEGACY_V2_TO_ENTERPRISE_MAPPING.md`
- `backend/docs/event_contracts_v1.md`
- `docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md`

