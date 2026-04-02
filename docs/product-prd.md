# Engineering Product Requirements Document (E-PRD)

## Personal AI Assistant Agent

### Version v3.0 (Production-Ready)

### Date: April 2026

---

# 1. Purpose

This document defines the complete production-grade architecture, system behavior, contracts, and implementation constraints for building a Personal AI Assistant Agent capable of executing real-world tasks via Slack.

This version includes:

* Explicit architecture
* Agent execution contracts
* Queue + orchestration design
* AI interaction schema
* Testing & validation requirements

---

# 2. System Architecture (MANDATORY)

## 2.1 Services

The system MUST be modular and service-oriented.

### Core Services

1. Slack Gateway Service

   * Handles Slack commands (/do, /call, /status, etc.)
   * Sends acknowledgments (<2s)

2. Orchestrator Service

   * Parses tasks
   * Manages task lifecycle
   * Dispatches jobs to queue

3. Agent Runner Service

   * Executes agent loop
   * Interfaces with AI model
   * Maintains execution state

4. Browser Automation Service

   * Playwright execution
   * Session management

5. Voice Service

   * Handles outbound calls (Vapi/Bland/Retell)

6. Approval Service

   * Manages approval requests
   * Handles user responses

7. Context Store Service

   * Secure retrieval of user data

8. Observability Service

   * Logging, tracing, replay

---

## 2.2 Communication

* Internal: Event-driven (queue-based)
* Queue: Redis (BullMQ) or AWS SQS
* APIs: REST for synchronous interactions

---

## 2.3 Data Flow

Slack → Gateway → Orchestrator → Queue → Agent Runner → (Browser/Voice) → Approval → Completion

---

# 3. Task Lifecycle (STRICT)

States:

* pending
* running
* waiting_for_approval
* completed
* failed
* cancelled

## Requirements

* Persist state in DB
* Support retry/resume
* Support cancellation at any state

---

# 4. Queue & Orchestration Design

## Queue Requirements

* FIFO with priority support
* Retry strategy: exponential backoff
* Dead Letter Queue required

## Job Schema

```
{
  task_id,
  user_id,
  type: "web" | "call",
  payload,
  priority,
  retries
}
```

---

# 5. AI Execution Engine

## 5.1 Agent Loop

1. Capture state (screenshot + DOM)
2. Send to AI
3. Receive structured action
4. Execute action
5. Validate result
6. Repeat

Constraints:

* Max cycles without progress: 3
* Max duration: 5 minutes

---

## 5.2 Action Schema (MANDATORY)

```
{
  "action": "click | type | scroll | wait | extract",
  "target": "selector | coordinates",
  "value": "optional",
  "confidence": 0-1,
  "reason": "string"
}
```

---

## 5.3 Validation Layer

* Must verify action success
* Detect no-op actions
* Trigger retry or failure

---

# 6. Prompting & AI Contract

## Input Structure

* Task goal
* Current state (DOM + screenshot)
* Previous actions
* Constraints

## Output Rules

* MUST return valid JSON
* MUST include reasoning
* MUST not hallucinate elements

---

# 7. Web Automation Module

## Requirements

* Playwright (headless Chromium)
* Persistent profile
* Isolated sessions per task

## Rules

* Retry interactions (min 3 attempts)
* Validate navigation success

---

# 8. Approval System

## Triggers

* Payments
* Irreversible actions
* Uncertainty

## Approval Object

```
{
  approval_id,
  task_id,
  action_summary,
  screenshot_url,
  status: pending | approved | rejected,
  expires_at
}
```

## Behavior

* Block execution
* Timeout handling required

---

# 9. Voice Module

## Requirements

* Real-time conversation
* Phone tree navigation

## Call Flow

* Resolve number
* Execute call
* Return transcript + summary

---

# 10. Context Store

## Requirements

* Structured schema
* Secure access

## Access Rules

* Load minimal required data
* Mask sensitive fields

---

# 11. Error Handling

## Conditions

* Timeout
* Element not found
* Site failure

## Behavior

* Screenshot
* Log
* Notify user

---

# 12. Observability

## MUST LOG

* All actions
* AI inputs/outputs
* Screenshots

## MUST SUPPORT

* Replay
* Debug trace

---

# 13. Security

* Secrets Manager required
* Encryption at rest
* No plaintext credentials

---

# 14. Testing & CI/CD (MANDATORY)

## Test Types

* Unit tests (agent logic)
* Integration tests (browser + AI)
* Replay tests

## CI/CD

* Automated test runs
* Deployment pipelines

---

# 15. Failure Recovery

## Requirements

* Checkpoints per step
* Resume from last valid state

---

# 16. Performance

* Ack <2s
* Concurrent tasks supported

---

# 17. Cost Controls

* Limit AI calls per task
* Budget caps per user

---

# 18. Acceptance Criteria

System complete only if:

* End-to-end execution works
* Approval system enforced
* Full logging available
* Recovery works

---

# 19. Engineering Constraints

* Modular architecture
* Queue-based execution
* Replayable tasks

---

# 20. Final Note

This system is a controlled autonomous agent. Safety, determinism, and observability take priority over speed.
