// ─── Auth ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  github_id: number;
  github_login: string;
  email: string | null;
  avatar_url: string | null;
  org_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ─── Repository ───────────────────────────────────────────────────────────────

export interface Repo {
  id: string;
  github_id: number;
  full_name: string;
  default_branch: string;
  is_active: boolean;
  language: string | null;
  org_id: string;
  created_at: string;
  updated_at: string;
}

export interface RepoUpdate {
  is_active?: boolean;
}

// ─── Scan ─────────────────────────────────────────────────────────────────────

export interface Scan {
  id: string;
  repo_id: string;
  pr_number: number | null;
  commit_sha: string;
  branch: string | null;
  trigger: string;
  status: string;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  findings_count: number;
  critical_count: number;
  high_count: number;
  created_at: string;
  updated_at: string;
}

export interface ManualScanRequest {
  repo_id: string;
  commit_sha: string;
  branch: string;
}

// ─── Finding ──────────────────────────────────────────────────────────────────

export interface Finding {
  id: string;
  scan_id: string;
  repo_id: string;
  tool: string;
  rule_id: string;
  file_path: string;
  line_start: number | null;
  line_end: number | null;
  snippet: string | null;
  severity: string;
  category: string;
  title: string;
  description: string | null;
  fingerprint: string;
  ai_severity: string | null;
  ai_explanation: string | null;
  ai_suggested_fix: string | null;
  confidence: number | null;
  ai_verdict: string | null;
  status: string;
  first_seen: string;
  last_seen: string;
  pr_number: number | null;
  commit_sha: string | null;
  package_name: string | null;
  package_version: string | null;
  cve_id: string | null;
  cwe_id: string | null;
  auto_fix_status: string | null;
  auto_fix_pr_url: string | null;
  auto_fix_pr_number: number | null;
  auto_fix_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface FindingUpdate {
  status: string;
}

export interface BulkFindingUpdate {
  finding_ids: string[];
  status: string;
}

export interface FindingEvent {
  id: string;
  finding_id: string;
  actor_id: string | null;
  action: string;
  old_value: string | null;
  new_value: string | null;
  comment: string | null;
  created_at: string;
}

// ─── Policy ───────────────────────────────────────────────────────────────────

export interface PolicyRules {
  fail_on: string[];
  max_critical: number | null;
  max_high: number | null;
  block_licenses: string[];
}

export interface Policy {
  id: string;
  org_id: string;
  name: string;
  is_active: boolean;
  rules: PolicyRules;
  created_at: string;
  updated_at: string;
}

export interface PolicyCreate {
  name: string;
  rules: PolicyRules;
}

export interface PolicyUpdate {
  name?: string;
  is_active?: boolean;
  rules?: PolicyRules;
}

// ─── Analytics ───────────────────────────────────────────────────────────────

export interface TimeSeriesPoint {
  date: string;
  opened: number;
  resolved: number;
}

export interface SeverityCount {
  severity: string;
  count: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface TopRule {
  rule_id: string;
  tool: string;
  count: number;
}

export interface TopRepo {
  full_name: string;
  count: number;
}

export interface MTTRBySeverity {
  severity: string;
  avg_hours: number;
}

export interface AnalyticsResponse {
  total_open: number;
  total_resolved: number;
  total_suppressed: number;
  time_series: TimeSeriesPoint[];
  by_severity: SeverityCount[];
  by_category: CategoryCount[];
  top_rules: TopRule[];
  top_repos: TopRepo[];
  mttr_by_severity: MTTRBySeverity[];
}

// ─── Shared ───────────────────────────────────────────────────────────────────

export type ScanStatus = 'pending' | 'running' | 'completed' | 'failed';
export type FindingStatus = 'open' | 'resolved' | 'suppressed' | 'false_positive';
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
