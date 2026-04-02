# Encryption at rest plan (T-011)

**Scope:** PostgreSQL columns and object storage blobs that may hold tokens, PII, or transcripts.

## Sensitive columns (identify)

| Location | Field | Risk | Phase |
|----------|-------|------|--------|
| `tasks` | `payload` (JSONB) | User intent, URLs, free text | Encrypt JSON or field-level before insert |
| Future `context` / user profile | phone, email, address | PII | Field-level AES-256-GCM or pgcrypto |
| Future `approvals` | `screenshot_url` | Indirect (URL to object) | Bucket policy + SSE |
| Object storage | Screenshot PNGs | Visual PII | SSE-S3 / SSE-KMS |

## Recommended approach

1. **Application-layer (KMS envelope)** for JSONB blobs: encrypt with DEK, wrap DEK with AWS KMS; store `ciphertext`, `iv`, `wrapped_dek` in JSON or separate columns. Works across app replicas; keys in KMS only.
2. **Alternative — pgcrypto in PostgreSQL** for column-level encryption with a single DB-managed key: simpler ops, weaker story for per-tenant keys and application-side masking before log.

**Choice for this codebase:** Prefer **KMS envelope in the application** for `tasks.payload` and context rows so logs and agents can mask before persist; align with AWS Secrets Manager for secrets (PRD §13).

## Migration plan (stub)

1. Add nullable columns `payload_enc`, `payload_meta` (or versioned wrapper).
2. Dual-write: new rows encrypted; background job migrates old rows.
3. Flip read path to decrypt; drop plaintext column after validation.
4. **Key rotation:** re-wrap DEKs with new KMS key version; no full re-encrypt of data if using envelope pattern (rotate CMK, re-wrap stored DEKs).

## Related

- `personal_ai/config/secrets.py` — runtime secrets, not data-at-rest keys.
- Future task: implement `encrypt_payload` / `decrypt_payload` helpers and wire into orchestrator before insert.
