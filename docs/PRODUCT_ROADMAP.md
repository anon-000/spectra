# Spectra: From Project to Product — Phased Roadmap

## Current State Summary

Spectra is a **security scanning SaaS** that auto-scans GitHub repos on every PR/push with 4 tools (SAST, SCA, Secrets, License), AI triage via Claude, and a web dashboard. The backend is ~85% complete, the frontend is ~50% (basic MVP). The core architecture is solid — async FastAPI, PostgreSQL, Redis/ARQ workers, Docker-composed.

---

## Phase 1: Polish & Ship the MVP (Priority: CRITICAL | Difficulty: Low-Medium)

*Goal: Make what exists actually usable end-to-end*

### 1.1 Complete Detail Pages (Easy | 2-3 days)
- **Finding detail page** — code snippet viewer, AI triage results (verdict, explanation, suggested fix), status actions, event timeline/audit trail
- **Scan detail page** — scan progress, tool-by-tool results, findings breakdown by severity/category, duration, error logs
- **Repo detail page** — scan history, finding trends, enable/disable toggle, last scan status

### 1.2 Auth Hardening (Easy | 1 day)
- JWT refresh token rotation (current tokens expire but never refresh)
- Proper logout (revoke token, not just clear localStorage)
- Protect against token in localStorage XSS — move to httpOnly cookies
- Add CSRF protection

### 1.3 API Rate Limiting (Easy | 0.5 day)
- Add `slowapi` or custom middleware for rate limiting
- Per-user and per-IP limits on API endpoints
- Separate limits for webhook endpoint

### 1.4 Input Validation & Error UX (Easy | 1 day)
- Schema validation on policy rules JSON (currently accepts anything)
- Frontend error boundaries with meaningful messages
- Loading skeletons and empty states on all pages
- Toast notifications for all mutations (create/update/delete)

### 1.5 Basic Testing Suite (Medium | 2-3 days)
- Mock GitHub API responses for webhook/scan tests
- API endpoint integration tests (auth, repos, scans, findings, policies)
- Scan orchestrator unit tests
- Frontend: at minimum test auth flow and critical user paths

---

## Phase 2: Differentiation & Stickiness (Priority: HIGH | Difficulty: Medium)

*Goal: Features that make users choose Spectra over running Semgrep themselves*

### 2.1 Real-Time Scan Updates (Medium | 2 days)
- WebSocket or SSE endpoint for live scan progress
- Frontend shows scan stages: cloning → SAST → SCA → Secrets → License → AI Triage → Done
- Real-time finding count updates on dashboard
- This is huge for UX — users currently have to refresh to see scan results

### 2.2 Finding Trend Analytics (Medium | 2-3 days)
- Time-series charts: findings opened vs resolved over time
- Mean time to remediate (MTTR) per severity
- Top vulnerable repos, most common rule violations
- Security posture score per repo/org
- This transforms the dashboard from a "list viewer" into an **actionable security tool**

### 2.3 Custom Scan Rules (Medium | 2 days)
- Upload custom Semgrep YAML rules per org
- Custom secret detection patterns (regex) for internal tokens/keys
- Custom license allowlist/blocklist
- Store in DB + S3, inject at scan time

### 2.4 RBAC — Role-Based Access Control (Medium | 3 days)
- Roles: `owner`, `admin`, `developer`, `viewer`
- Owners manage org settings, billing, members
- Admins manage policies, suppress findings
- Developers see their repos' findings, can mark false positives
- Viewers read-only access
- Essential for teams > 3 people

### 2.5 Finding Grouping & Smart Dedup (Medium | 2 days)
- Group related findings (same rule across multiple files)
- Show "X occurrences" instead of X individual findings
- Cross-PR finding tracking — "this finding has been open for 5 PRs"
- Reduces noise dramatically

---

## Phase 3: Enterprise Readiness (Priority: HIGH | Difficulty: Medium-Hard)

*Goal: Features required for any team to adopt this seriously*

### 3.1 Multi-Org & Team Support (Hard | 4-5 days)
- User can belong to multiple organizations
- Org switching in the UI
- Invitation system (invite by email/GitHub username)
- Org-level settings (default policies, notification preferences)

### 3.2 SSO / SAML (Hard | 3-4 days)
- Enterprise SSO via SAML 2.0 or OpenID Connect
- Integration with Okta, Azure AD, Google Workspace
- Auto-provisioning users from IdP

### 3.3 Compliance Reporting (Medium | 3 days)
- Generate PDF/CSV compliance reports
- SBOM export (CycloneDX JSON/XML, SPDX)
- Vulnerability disclosure report format
- Audit log export for SOC2/ISO27001 evidence
- Scheduled report delivery via email

### 3.4 GitLab & Bitbucket Support (Hard | 5-7 days)
- Abstract the GitHub integration into a SCM provider interface
- Add GitLab webhook handler + MR comments
- Add Bitbucket webhook handler + PR comments
- Triples your addressable market

### 3.5 API Keys & CI/CD Integration (Medium | 2 days)
- Generate API keys for programmatic access
- CLI tool or GitHub Action for manual scan triggers
- JSON output format for CI/CD pipeline consumption
- Webhook callbacks for scan completion

---

## Phase 4: Scale & Monetization (Priority: MEDIUM | Difficulty: Hard)

*Goal: Run this as a real business*

### 4.1 Billing & Subscription (Hard | 5-7 days)
- Stripe integration for payments
- Tiered plans: Free (3 repos), Pro (unlimited repos, AI triage), Enterprise (SSO, RBAC, SLA)
- Usage tracking (scans/month, AI triage calls)
- Plan limits enforcement in middleware

### 4.2 Kubernetes Deployment & Auto-Scaling (Hard | 3-4 days)
- Helm chart for k8s deployment
- Horizontal pod autoscaling for workers based on queue depth
- Job isolation — each scan in its own container (security)
- Resource limits per scan (CPU, memory, timeout)

### 4.3 Observability Stack (Medium | 2 days)
- Prometheus metrics (scan duration, queue depth, error rates, AI triage latency)
- Grafana dashboards
- OpenTelemetry tracing (request → scan → tools → AI → notification)
- Sentry for error tracking
- PagerDuty/OpsGenie alerts

### 4.4 Caching & Performance (Medium | 2 days)
- Redis caching for dashboard queries (finding counts, repo stats)
- Cursor-based pagination (current offset pagination won't scale past 100k findings)
- Database query optimization — composite indexes for common filters
- CDN for frontend assets

### 4.5 Multi-Region & Data Residency (Hard | ongoing)
- Deploy in EU/US/APAC regions
- Data residency controls (findings stay in user's region)
- Required for enterprise adoption in regulated industries

---

## Phase 5: Competitive Moat (Priority: MEDIUM | Difficulty: Hard)

*Goal: Features that make switching away painful (in a good way)*

### 5.1 AI Fix Suggestions with Auto-PR (Hard | 4-5 days)
- Beyond just suggesting fixes — generate a fix PR automatically
- Use Claude to write the code patch
- Create a branch, commit the fix, open a PR
- User reviews and merges — one-click remediation
- **This is the killer feature** that no competitor does well

### 5.2 Dependency Update Bot (Medium | 3 days)
- When SCA finds a vulnerable dependency, auto-create a PR bumping the version
- Verify the update doesn't break anything (run tests if CI is configured)
- Similar to Dependabot but integrated with your scanning

### 5.3 Security Knowledge Base (Medium | 3 days)
- Per-org knowledge base of past decisions
- "Last time this rule fired, team marked it as false positive because..."
- AI learns from org's triage patterns over time
- Automatically suppress findings matching historical patterns

### 5.4 IDE Extensions (Hard | 5+ days)
- VS Code extension showing findings inline
- JetBrains plugin
- Real-time scanning as you code (pre-commit)
- Shift-left to the maximum

### 5.5 Webhook & Integration Platform (Medium | 3 days)
- Outgoing webhooks for scan events
- Jira integration (auto-create tickets for critical findings)
- PagerDuty integration (alert on-call for critical findings)
- Microsoft Teams notifications
- Custom webhook templates

---

## Priority Matrix — What to Do First

| Priority | Feature | Difficulty | Impact | Timeline |
|----------|---------|-----------|--------|----------|
| 1 | Complete detail pages | Easy | High | **Now** |
| 2 | Auth hardening (httpOnly cookies, refresh) | Easy | High | **Now** |
| 3 | Real-time scan updates (WebSocket) | Medium | High | **Now** |
| 4 | Rate limiting | Easy | Medium | **Now** |
| 5 | Loading states, error boundaries | Easy | Medium | **Now** |
| 6 | Finding trend analytics | Medium | High | Week 2 |
| 7 | RBAC | Medium | High | Week 2-3 |
| 8 | Basic test suite | Medium | High | Week 2-3 |
| 9 | Custom scan rules | Medium | Medium | Week 3 |
| 10 | API keys & CI/CD integration | Medium | High | Week 3-4 |
| 11 | Multi-org support | Hard | High | Month 2 |
| 12 | GitLab/Bitbucket support | Hard | Very High | Month 2-3 |
| 13 | AI auto-fix PRs | Hard | Very High | Month 2-3 |
| 14 | Billing (Stripe) | Hard | Critical | Month 3 |
| 15 | K8s deployment & scaling | Hard | High | Month 3 |
| 16 | Compliance reporting | Medium | High | Month 3-4 |
| 17 | SSO/SAML | Hard | High | Month 4+ |
| 18 | IDE extensions | Hard | Medium | Month 5+ |

---

## Top 3 "Bang for Buck" Recommendations

1. **Real-time scan updates + completed detail pages** — Makes the product feel alive and professional. Without these, it feels like a prototype. Low-medium effort, massive UX impact.

2. **AI auto-fix PRs** — This is your killer differentiator. You already have Claude integration and the fix suggestions. Going from "here's what to fix" to "here's a PR that fixes it" is transformational. Hard to build, but it's the feature that sells the product.

3. **Finding analytics dashboard** — Transforms Spectra from "a scanner" into "a security posture platform." CISOs buy dashboards with trend lines, not raw findings lists. Medium effort, directly tied to monetization.
