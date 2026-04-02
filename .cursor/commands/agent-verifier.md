# Verifier only (QA / tests)

**Scope to verify (PR, feature, or files):**

<!-- What was implemented; link or paste summary -->

---

Act as **VERIFIER** using subagent **personal-ai-verifier** (or label **Role: VERIFIER**).

- Think like a failure tester. Output: Test Scenarios (happy + edge + failure), Bugs/Issues Found, Missing Cases, Risk Level (Low/Medium/High), Suggested Fixes.
- Check: requirements met, edge cases, retries/timeouts, recoverability, logs/debuggability, state correctness, HITL behavior.
- **Do not** rewrite the whole app; suggest targeted fixes for **Executor**.
