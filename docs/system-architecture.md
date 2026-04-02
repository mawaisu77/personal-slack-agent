# System Architecture — Visual Reference

**Source:** `docs/product-prd.md` v3.0 · **Planning:** `planning/epics.md`, `planning/phases.md`

This document provides **logical** and **infrastructure** views. Diagrams use [Mermaid](https://mermaid.js.org/) (renders in GitHub, GitLab, many IDEs, and Markdown preview).

---

## 1. System context (C4 Level 1)

Who interacts with the system and which external systems are involved.

```mermaid
flowchart LR
  subgraph actors["Actors"]
    U[("User")]
  end

  subgraph slack_cloud["Slack platform"]
    SL[Slack Workspace]
  end

  subgraph pai["Personal AI Assistant — System boundary"]
    SYS["Controlled autonomous agent\n(Slack + orchestration + agents)"]
  end

  subgraph external["External capabilities"]
    AI["Claude API\n(structured actions)"]
    VO["Voice providers\n(Vapi / Bland / Retell)"]
    TW["Telephony\n(Twilio / carrier)"]
    WEB["Target websites\n(web automation)"]
  end

  U --> SL
  SL <-->|"Commands / approvals\n/async updates"| SYS
  SYS <-->|"HTTPS"| AI
  SYS <-->|"HTTPS"| VO
  VO --> TW
  SYS <-->|"HTTPS"| WEB
```

---

## 2. Logical service architecture (C4 Level 2 — containers)

Mandatory modular services from the PRD, plus queue and persistence.

```mermaid
flowchart TB
  subgraph ingress["Ingress & control plane"]
    GW["Slack Gateway Service\n(/do /call /status /cancel /history)\nack < 2s"]
    ORCH["Orchestrator Service\nparse · lifecycle · dispatch"]
  end

  subgraph async["Async execution plane"]
    Q[("Job queue\nRedis / SQS\nFIFO + priority + DLQ")]
    RUN["Agent Runner Service\nagent loop · AI I/O · checkpoints"]
  end

  subgraph agents["Tooling backends"]
    BR["Browser Automation Service\nPlaywright · profiles · isolated contexts"]
    VS["Voice Service\noutbound · realtime · transcripts"]
  end

  subgraph data_services["Shared domain services"]
    APPR["Approval Service\nblock · timeout · Slack interactions"]
    CTX["Context Store Service\nminimal fields · masked access"]
    OBS["Observability Service\nlogs · traces · replay"]
  end

  subgraph persistence["Data stores"]
    PG[("PostgreSQL\ntasks · checkpoints\napprovals · audit")]
    OBJ[("Object storage\nS3 / R2\nscreenshots · artifacts")]
  end

  subgraph secrets["Secrets"]
    SM["Secrets Manager\n(no plaintext credentials)"]
  end

  GW --> ORCH
  ORCH --> PG
  ORCH --> Q
  Q --> RUN
  RUN --> BR
  RUN --> VS
  RUN --> APPR
  RUN --> CTX
  RUN --> OBS
  APPR --> PG
  APPR --> GW
  CTX --> PG
  BR --> OBJ
  APPR --> OBJ
  GW --> SM
  ORCH --> SM
  RUN --> SM
  VS --> SM
```

---

## 3. Runtime data flow (primary path)

PRD §2.3: Slack → Gateway → Orchestrator → Queue → Agent Runner → (Browser | Voice) → Approval → Completion.

```mermaid
flowchart LR
  S[Slack] --> G[Gateway]
  G --> O[Orchestrator]
  O --> Q[Queue]
  Q --> R[Agent Runner]
  R --> B[Browser]
  R --> V[Voice]
  R --> A[Approval]
  A --> O
  R --> X[Complete / Fail]
  O --> P[(PostgreSQL)]
  R --> P
  B --> Z[(Screenshots)]
```

---

## 4. Sequence — `/do` web task with approval checkpoint

Illustrates blocking approval, screenshot URL, and resume.

```mermaid
sequenceDiagram
  autonumber
  participant U as User
  participant SL as Slack
  participant GW as Slack Gateway
  participant O as Orchestrator
  participant Q as Queue
  participant R as Agent Runner
  participant B as Browser / Playwright
  participant AI as Claude API
  participant AP as Approval Service
  participant ST as Object storage
  participant DB as PostgreSQL

  U->>SL: /do goal
  SL->>GW: slash command
  GW->>O: create task
  O->>DB: pending
  GW-->>U: ack < 2s
  O->>Q: enqueue job (type=web)
  Q->>R: deliver job
  R->>DB: running
  loop Agent loop (max duration / no-progress limits)
    R->>B: capture DOM + screenshot
    B->>ST: store screenshot
    R->>AI: state + goal + history
    AI-->>R: structured action JSON
    R->>B: execute action
    alt irreversible / payment / uncertainty
      R->>DB: waiting_for_approval
      R->>AP: create approval (+ screenshot URL)
      AP->>SL: message + buttons
      U->>SL: Approve / Reject
      SL->>AP: interaction
      AP->>R: resume or abort
    end
  end
  R->>DB: completed | failed
  SL-->>U: result / summary
```

---

## 5. Task lifecycle (strict states)

```mermaid
stateDiagram-v2
  [*] --> pending
  pending --> running
  running --> waiting_for_approval
  running --> completed
  running --> failed
  running --> cancelled
  waiting_for_approval --> running : approved
  waiting_for_approval --> failed : rejected / timeout
  waiting_for_approval --> cancelled
  pending --> cancelled
  completed --> [*]
  failed --> [*]
  cancelled --> [*]
```

---

## 6. Infrastructure & deployment topology

Logical cloud layout: **API / gateway** path vs **worker** path vs **data plane**. Adjust regions and HA for your provider.

```mermaid
flowchart TB
  subgraph internet["Public internet"]
    SLK["Slack API\n(events · commands · interactions)"]
    USR["Users"]
  end

  subgraph edge["Edge / entry"]
    LB["Load balancer / API gateway\nTLS termination · rate limits"]
  end

  subgraph compute_api["Compute — control plane"]
    API["Slack Gateway + Orchestrator API\n(stateless · horizontal scale)"]
  end

  subgraph compute_workers["Compute — workers"]
    W1["Agent Runner + Browser\n(Playwright · heavier CPU/RAM)"]
    W2["Agent Runner + Voice client\n(I/O bound)"]
  end

  subgraph data_plane["Data plane"]
    RDS[("PostgreSQL\nHA / backups · encryption at rest")]
    REDIS[("Redis\nqueue · optional cache")]
    S3[("S3 / R2\nscreenshots · traces")]
  end

  subgraph sec["Security & config"]
    KMS["KMS / encryption keys"]
    SECSM["Secrets Manager"]
  end

  subgraph external_apis["External APIs"]
    CLAUDE["Claude API"]
    VAPI["Voice API"]
  end

  USR --> SLK
  SLK --> LB
  LB --> API
  API --> RDS
  API --> REDIS
  API --> SECSM
  REDIS --> W1
  REDIS --> W2
  W1 --> RDS
  W2 --> RDS
  W1 --> S3
  W1 --> CLAUDE
  W2 --> VAPI
  API --> KMS
  RDS --> KMS
```

---

## 7. Network trust zones (conceptual)

Useful for firewall rules and least-privilege IAM.

```mermaid
flowchart LR
  subgraph untrusted["Untrusted"]
    SL[Slack / public web targets]
  end

  subgraph dmz["DMZ / edge"]
    LB2[LB + WAF]
  end

  subgraph trusted["Trusted — app tier"]
    APP[Gateway · Orchestrator API]
  end

  subgraph workers["Trusted — worker tier"]
    WRK[Agent runners]
  end

  subgraph dataz["Data zone — restricted"]
    DB2[(Postgres)]
    RD2[(Redis)]
    OB2[(Object store)]
  end

  SL --> LB2 --> APP
  APP --> RD2
  APP --> WRK
  WRK --> DB2
  WRK --> OB2
  WRK --> SL
```

---

## 8. Observability path

PRD §12: log actions, AI I/O, screenshots; support replay/debug.

```mermaid
flowchart LR
  R[Agent Runner] --> L[Structured logs + trace IDs]
  R --> T[Trace / replay blob]
  L --> AGG[Log aggregation]
  T --> OB[(Observability store\n+ replay harness)]
  L --> DSH[Dashboards / alerts]
```

---

## Related documents

| Document | Purpose |
|----------|---------|
| `docs/product-prd.md` | Authoritative requirements |
| `planning/epics.md` | Epic breakdown |
| `planning/phases.md` | Delivery phases |
| `planning/dependencies.json` | Task graph |

---

## Export tips

- **PNG/SVG from Mermaid:** use [Mermaid Live Editor](https://mermaid.live), CLI `mmdc`, or IDE export.
- **Diagrams as Code:** keep this file as the source of truth; regenerate images in CI if needed.
