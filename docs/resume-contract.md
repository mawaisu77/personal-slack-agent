# Resume contract (orchestrator ↔ agent runner)

**Source:** PRD §15 · Task **T-002**

## Data

- Checkpoints are stored in `checkpoints` (`task_id`, monotonic `sequence`, `payload_json`).
- `append_checkpoint` allocates the next `sequence` per `task_id` (no gaps required for correctness; duplicates are prevented by `UNIQUE (task_id, sequence)`).

## Resume

1. Before starting or restarting the agent loop, the runner calls `latest_checkpoint(task_id)`.
2. If a row exists, `payload_json` is the last persisted step state (step index, DOM hash, last action id, etc.).
3. If none exists, the runner starts from the task’s initial `tasks.payload` as defined by the orchestrator.

## Idempotency

- Re-running `append_checkpoint` after a failure creates a **new** sequence value; callers must not reuse the same `sequence` manually.
- The runner should flush checkpoints after each validated loop iteration so “last valid checkpoint” always matches PRD §15.

## Owner

- **Writes:** Agent Runner (E-RUN) after successful step validation.
- **Reads:** Agent Runner on startup and after worker restart.
