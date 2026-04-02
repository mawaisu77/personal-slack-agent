
# Personal AI Assistant Agent

**Web Automation + Voice Calling via Slack Interface**

## Overview

This project is a personal AI assistant that executes real-world tasks through natural language commands sent via Slack (and optionally SMS). The system automates web interactions and performs phone calls on behalf of the user, acting like a highly capable digital assistant.

The assistant supports:

* Web automation (orders, forms, registrations, returns)
* Voice calls (reservations, scheduling, customer service)
* Human-in-the-loop confirmation before critical actions

---

## Key Features

### 1. Slack-Based Command Interface

* `/do` → Web automation tasks
* `/call` → Phone call tasks
* `/status` → Check task progress
* `/cancel` → Abort current task
* `/history` → View past tasks

### 2. Web Automation

* Navigate any website
* Fill forms using stored personal data
* Place orders and complete purchases
* Handle logins and sessions
* CAPTCHA solving (fallback to manual)

### 3. Voice Calling

* Make outbound calls
* Navigate phone trees
* Conduct real-time conversations
* Provide summaries and transcripts

### 4. Approval Workflow

* Required before:

  * Payments
  * Irreversible actions
* Slack-based approve/reject system
* Screenshot + summary preview

### 5. Personal Context Integration

* Secure storage of:

  * Personal info
  * Family details
  * Preferences
  * Accounts
  * Vehicles & insurance

### 6. Audit & Logging

* Full action logs
* Screenshots for each step
* Error tracking
* Task history

---

## System Architecture

### High-Level Flow

1. User sends command via Slack
2. System parses intent using AI
3. Task routed to:

   * Web Automation Agent OR
   * Voice Agent
4. Execution begins
5. System pauses for approval (if required)
6. Task completes and reports results

---

## Tech Stack

### Backend

* Python (FastAPI) or Node.js
* Redis (queue + caching)
* PostgreSQL (task logs)

### AI Layer

* Claude API (Sonnet / Opus)
* Agent orchestration loop

### Web Automation

* Playwright (headless browser)
* Persistent browser sessions

### Voice AI

* Vapi / Bland / Retell
* Twilio (optional fallback)

### Integrations

* Slack Bolt SDK
* Google Places API (phone lookup)

### Storage

* AWS S3 / Cloudflare R2 (screenshots)
* AWS Secrets Manager / 1Password (credentials)

### Deployment

* Railway / Render / AWS EC2
* Docker

---

## Core Modules

### 1. Orchestrator

* Parses commands
* Routes tasks
* Manages execution lifecycle

### 2. Web Automation Agent

* Executes browser actions via Playwright
* Uses AI-driven action loop:

  * Screenshot → AI → Action → Execute

### 3. Voice Agent

* Places calls
* Handles conversations
* Returns summaries/transcripts

### 4. Slack Interface

* Command handling
* Notifications and updates
* Approval UI

### 5. Context Store

* Secure personal data
* Structured JSON/YAML format

### 6. Approval System

* Interactive Slack messages
* Blocking execution until confirmation

---

## Security Requirements

* No plaintext credentials
* Encrypted storage for all sensitive data
* Secure browser session handling
* Private Slack channels only
* Mandatory approval for all purchases
* Full audit logging
* API key rotation
* Encrypted call recordings (auto-delete after 30 days)

---

## Error Handling

* Detect stuck states (no progress)
* Timeout handling (>5 minutes)
* Screenshot-based debugging
* User escalation when needed
* Clear error reporting

---

## Milestones

| Phase | Description                    | Timeline |
| ----- | ------------------------------ | -------- |
| 1     | Slack bot + Amazon automation  | Week 1–2 |
| 2     | General web automation + forms | Week 3–4 |
| 3     | Voice calling module           | Week 4–5 |
| 4     | Security, polish, deployment   | Week 5–6 |

---

## Estimated Costs

| Service     | Monthly Cost |
| ----------- | ------------ |
| AI (Claude) | $50–200      |
| Voice AI    | $30–100      |
| CAPTCHA     | $5–20        |
| Hosting     | $20–50       |
| **Total**   | **$100–400** |

---

## Developer Requirements

### Must-Have

* Playwright (production experience)
* AI agents / Claude API
* Slack bot development
* Secure credential handling
* Backend + API development

### Nice-to-Have

* Voice AI platforms
* Agent frameworks
* Security expertise
* Automation systems experience

---

## Challenges

* Dynamic website changes
* CAPTCHA & anti-bot systems
* Stateful task execution
* Voice conversation edge cases
* Secure handling of sensitive data

---

## Future Enhancements

* Multi-user support
* Advanced task planning
* Learning user preferences
* Improved voice capabilities
* Expanded integrations

---

## Maintenance

* Monthly updates for site changes
* Bug fixes within 48 hours
* Security reviews
* Feature expansion support

---

## Getting Started (Planned)

```bash
# Clone repo
git clone <repo-url>

# Install dependencies
npm install
# or
pip install -r requirements.txt

# Run server
npm run dev
# or
uvicorn app:app --reload
```
