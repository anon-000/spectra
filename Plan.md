Let me think about this carefully — an MVP that's actually shippable, not overengineered, but impressive enough to demonstrate value.

---

## MVP Scope — What to Build

The core pitch: **"Plug into your GitHub repo, get unified security scanning on every PR with smart noise reduction and a dashboard to manage findings."**

**MVP Features (keep it tight):**

**1. GitHub App Integration** — User installs your GitHub App, selects repos, done. No CLI setup, no Docker config. The app listens for PR webhooks and triggers scans automatically.

**2. Four Core Scans** — SAST (Semgrep), SCA (osv-scanner + reachability-lite), Secrets (Trufflehog with verification), License Compliance (CycloneDX + policy check). Same as Hela's foundation but running as a service.

**3. PR Comments with Inline Findings** — Post findings directly as PR review comments on the exact line. Developers see issues in their natural workflow, no context switching. Include a severity badge and a one-line explanation.

**4. AI Triage** — For each finding, pass the code context to an LLM and classify it as likely true positive, likely false positive, or needs review. This alone cuts noise by 50%+ and is your biggest differentiator over raw Hela.

**5. Web Dashboard** — Simple dashboard showing: all repos connected, findings per repo, findings over time, and a finding detail view where security teams can triage (mark as false positive, accepted risk, or needs fix). No fancy analytics yet, just the basics.

**6. Policy Engine** — YAML-based like Hela but configured via the dashboard. Set thresholds per severity, block PRs or just warn. Start simple, iterate later.

**7. Slack Notifications** — Alert on new critical/high findings and pipeline failures. Reuse Hela's concept but cleaner.

---

## Components & Architecture

Here's what the system looks like:

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL                                  │
│                                                                  │
│   GitHub ──webhook──▶  API Gateway  ◀──────── Web Dashboard     │
│          ◀──PR comments──┘    │                (React SPA)       │
│                               │                     │            │
│   Slack  ◀──alerts────────────┼─────────────────────┘            │
└───────────────────────────────┼──────────────────────────────────┘
                                │
┌───────────────────────────────┼──────────────────────────────────┐
│                        BACKEND                                   │
│                               ▼                                  │
│                     ┌──────────────────┐                         │
│                     │   Core API       │  (FastAPI)              │
│                     │   - Auth/Onboard │                         │
│                     │   - Webhook Rx   │                         │
│                     │   - Findings CRUD│                         │
│                     │   - Policy Eval  │                         │
│                     └────────┬─────────┘                         │
│                              │                                   │
│                              ▼                                   │
│                     ┌──────────────────┐                         │
│                     │   Task Queue     │  (Redis + Celery/ARQ)   │
│                     │                  │                         │
│                     └────────┬─────────┘                         │
│                              │                                   │
│              ┌───────────────┼───────────────┐                   │
│              ▼               ▼               ▼                   │
│     ┌──────────────┐ ┌─────────────┐ ┌──────────────┐           │
│     │ Scan Worker  │ │ Scan Worker │ │ Scan Worker  │  (k8s Job │
│     │              │ │             │ │              │   or ECS)  │
│     │ - git clone  │ │             │ │              │           │
│     │ - semgrep    │ │             │ │              │           │
│     │ - trufflehog │ │             │ │              │           │
│     │ - osv-scanner│ │             │ │              │           │
│     │ - cyclonedx  │ │             │ │              │           │
│     └──────┬───────┘ └──────┬──────┘ └──────┬───────┘           │
│            │                │               │                    │
│            ▼                ▼               ▼                    │
│     ┌───────────────────────────────────────────┐                │
│     │          Results Normalizer               │                │
│     │  - Unified finding schema                 │                │
│     │  - Dedup (hash-based)                     │                │
│     │  - AI Triage (LLM call)                   │                │
│     └─────────────────────┬─────────────────────┘                │
│                           │                                      │
│                           ▼                                      │
│     ┌───────────────────────────────────────────┐                │
│     │              PostgreSQL                    │                │
│     │  - repos, findings, policies, users        │                │
│     │              S3/MinIO                       │                │
│     │  - raw scan artifacts, SBOMs               │                │
│     └───────────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown & Responsibilities

**1. Core API (FastAPI + Python)**

This is the brain. Handles:
- **GitHub OAuth** — User signs in with GitHub, installs the GitHub App, grants repo access
- **Webhook receiver** — Listens for `pull_request.opened`, `pull_request.synchronize`, and `push` events
- **Scan orchestration** — When a webhook comes in, creates a scan job with metadata (repo URL, PR number, commit SHAs, branch info) and pushes it to the task queue
- **Findings CRUD** — REST endpoints for the dashboard to list/filter/update findings
- **Policy evaluation** — After scan completes, evaluate the policy and decide pass/fail, then call GitHub Checks API to set the PR status
- **GitHub PR commenting** — Post inline review comments for each finding

**2. Task Queue (Redis + ARQ or Celery)**

Simple job queue. A scan request comes in, gets queued, a worker picks it up. Use ARQ over Celery for the MVP — it's lighter, async-native, and Python-based which fits FastAPI well. Redis handles both the queue and short-lived caching (like scan status polling).

**3. Scan Workers**

This is where the actual security tools run. Each worker:
- Clones the repo (or just the PR diff commits for speed)
- Runs all four tools in parallel within the worker
- Collects raw JSON output from each tool
- Pushes results back to the Results Normalizer

For MVP, these can just be Celery/ARQ workers running on the same infra. Later you'd isolate them as k8s Jobs or Firecracker VMs for security. Each worker runs in a Docker container that has Semgrep, Trufflehog, osv-scanner, and CycloneDX pre-installed.

**4. Results Normalizer**

This is the key piece that Hela lacks sophistication in. It takes raw output from four different tools and converts everything into a **unified finding schema**:

```
Finding {
    id: uuid
    repo_id: FK
    scan_id: FK
    source_tool: "semgrep" | "trufflehog" | "osv-scanner" | "cyclonedx"
    type: "sast" | "sca" | "secret" | "license"
    severity: "critical" | "high" | "medium" | "low"
    title: string
    description: string
    file_path: string
    line_start: int
    line_end: int
    code_snippet: string
    cwe_id: optional
    cve_id: optional
    confidence: float          # from AI triage
    ai_verdict: "true_positive" | "false_positive" | "needs_review"
    status: "open" | "triaged" | "false_positive" | "accepted_risk" | "fixed"
    fingerprint: string        # hash for dedup across scans
    first_seen: datetime
    last_seen: datetime
    pr_number: optional
    commit_sha: string
}
```

**Deduplication** works by computing a fingerprint hash from (tool + rule_id + file_path + code_snippet_normalized). If the same finding shows up in consecutive scans, update `last_seen` instead of creating a duplicate.

**AI Triage** — For each new finding, send the code snippet + surrounding context + the rule description to Claude/GPT and ask: "Is this a true positive? Rate confidence 0-1 and explain briefly." Store the verdict and confidence. This is a simple prompt, doesn't need anything fancy for MVP.

**5. PostgreSQL**

Core data model (simplified):

```
users          → id, github_id, email, name
organizations  → id, name, github_org_id
repos          → id, org_id, github_repo_id, name, default_branch, scan_enabled
scans          → id, repo_id, trigger_type (pr/push/manual/scheduled), 
                 status (queued/running/completed/failed), commit_sha, 
                 pr_number, started_at, completed_at
findings       → (schema above)
policies       → id, org_id, repo_id (nullable for org-wide), policy_yaml, active
finding_events → id, finding_id, action (status_change/comment), user_id, 
                 old_value, new_value, timestamp  # audit trail
```

**6. Web Dashboard (React)**

Keep it minimal for MVP. Four pages:

- **Repos page** — List connected repos, toggle scanning on/off, see last scan status
- **Findings page** — Filterable table (by repo, severity, type, status, AI verdict). Bulk actions (mark as false positive, etc.)
- **Finding detail** — Code snippet, tool info, AI explanation, timeline of status changes, link to GitHub file
- **Settings** — Policy config (form-based, generates YAML behind the scenes), Slack webhook URL, notification preferences

---

## The Flow End-to-End

Here's what happens when a developer opens a PR:

```
1. Developer opens PR on GitHub

2. GitHub sends webhook (pull_request.opened) to your API
   → API receives: repo name, PR #, head SHA, base branch

3. API creates a Scan record (status: queued) in Postgres
   → Pushes job to Redis queue
   → Sets GitHub Check status to "pending" via Checks API

4. Scan Worker picks up the job
   → git clone --depth=1 --branch=<pr_branch> <repo_url>
   → Runs in parallel:
      • semgrep --config=auto --json
      • trufflehog git file://./repo --json
      • osv-scanner --lockfile=./repo/package-lock.json --json
      • cyclonedx-cli analyze ./repo --output-format json
   → Collects all raw JSON outputs

5. Results Normalizer processes outputs
   → Converts each tool's output to unified Finding schema
   → Computes fingerprint hashes, deduplicates against existing findings
   → For NEW findings: calls LLM API for AI triage
   → Stores all findings in Postgres

6. Policy Engine evaluates
   → Loads policy for this repo (or org default)
   → Counts findings by severity and type
   → Determines: pass or fail

7. API posts results back to GitHub
   → Sets Check status to success/failure via Checks API
   → Posts inline PR review comments for each finding
     (includes severity, description, AI confidence, fix suggestion)

8. Notifications
   → If critical/high findings found: sends Slack alert
   → If policy failed: includes failure reason in Slack message

9. Dashboard reflects new scan results in real-time
```

---

## Tech Stack for MVP

| Component | Choice | Why |
|---|---|---|
| API | FastAPI (Python) | Fast to build, async-native, you know Python well |
| Queue | Redis + ARQ | Lightweight, async, simpler than Celery for MVP |
| DB | PostgreSQL | Solid, handles everything you need |
| Object Store | S3 or MinIO | Raw scan artifacts, SBOMs |
| Scan Workers | Docker containers with tools pre-installed | Simple, portable |
| Dashboard | React + Tailwind | Standard, fast to build |
| AI Triage | Claude API (Sonnet) | Good balance of quality and cost for code analysis |
| Auth | GitHub OAuth + JWT | Your users are already on GitHub |
| Deployment | Single VPS or small k8s cluster | Don't over-engineer infra for MVP |

---

## What NOT to Build in MVP

Keep this list pinned — scope creep will kill you:

- No multi-SCM support (GitHub only for now)
- No DAST or container scanning (add later)
- No RBAC/multi-tenant (single-tenant is fine for first 10 customers)
- No custom rule builder UI (users can provide custom Semgrep rules via repo config)
- No SARIF/DefectDojo integration (export later)
- No reachability analysis (complex, add in v2)
- No scheduled/periodic scans (PR-triggered only for MVP)
- No self-hosted option (SaaS only)

---

Want me to start building any of these components? I could set up the project structure with the FastAPI backend, the scan worker architecture, and the data models — or we could start with a detailed technical design doc first. What's your preferred approach?