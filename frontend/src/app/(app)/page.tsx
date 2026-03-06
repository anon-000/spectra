'use client';

import useSWR from 'swr';
import { reposApi } from '@/lib/api';
import { scansApi } from '@/lib/api';
import { findingsApi } from '@/lib/api';
import { ShieldAlert, ScanSearch, GitBranch, AlertTriangle, TrendingUp, Activity } from 'lucide-react';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SeverityBadge } from '@/components/ui/SeverityBadge';
import { formatDate, shortSha } from '@/lib/utils';
import Link from 'next/link';

function StatCard({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: number | string; color: string }) {
  return (
    <div className="bg-[#141414] rounded-2xl border border-white/5 p-6 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-slate-400 text-sm">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{value}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: repos } = useSWR('repos', () => reposApi.list());
  const { data: scans } = useSWR('scans-recent', () => scansApi.list({ page_size: 5 }));
  const { data: findings } = useSWR('findings-recent', () => findingsApi.list({ page_size: 5, status: 'open' }));
  const { data: criticalFindings } = useSWR('findings-critical', () => findingsApi.list({ severity: 'critical', status: 'open', page_size: 1 }));

  const openCount = findings?.length ?? 0;
  const criticalCount = criticalFindings?.length ?? 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-1 text-sm">Security overview for your organization</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard icon={GitBranch} label="Repositories" value={repos?.length ?? '—'} color="bg-indigo-500/80" />
        <StatCard icon={ScanSearch} label="Total Scans" value={scans?.length ?? '—'} color="bg-blue-500/80" />
        <StatCard icon={ShieldAlert} label="Open Findings" value={openCount} color="bg-orange-500/80" />
        <StatCard icon={AlertTriangle} label="Critical Open" value={criticalCount} color="bg-red-500/80" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Recent Scans */}
        <div className="bg-[#141414] rounded-2xl border border-white/5 overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
            <div className="flex items-center gap-2 text-white font-semibold">
              <Activity size={16} className="text-indigo-400" />
              Recent Scans
            </div>
            <Link href="/scans" className="text-xs text-indigo-400 hover:text-indigo-300 transition">View all →</Link>
          </div>
          <div className="divide-y divide-white/5">
            {!scans ? (
              <div className="px-6 py-8 text-center text-slate-500 text-sm">Loading...</div>
            ) : scans.length === 0 ? (
              <div className="px-6 py-8 text-center text-slate-500 text-sm">No scans yet</div>
            ) : scans.map((s) => (
              <Link key={s.id} href={`/scans/${s.id}`} className="flex items-center justify-between px-6 py-3.5 hover:bg-white/5 transition group">
                <div>
                  <p className="text-sm text-white font-medium group-hover:text-indigo-300 transition">{shortSha(s.commit_sha)} · {s.branch ?? 'unknown'}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{formatDate(s.created_at)}</p>
                </div>
                <div className="flex items-center gap-3">
                  {s.critical_count > 0 && <span className="text-xs text-red-400 font-medium">{s.critical_count} critical</span>}
                  <StatusBadge status={s.status} />
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Open Findings */}
        <div className="bg-[#141414] rounded-2xl border border-white/5 overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
            <div className="flex items-center gap-2 text-white font-semibold">
              <TrendingUp size={16} className="text-orange-400" />
              Open Findings
            </div>
            <Link href="/findings" className="text-xs text-indigo-400 hover:text-indigo-300 transition">View all →</Link>
          </div>
          <div className="divide-y divide-white/5">
            {!findings ? (
              <div className="px-6 py-8 text-center text-slate-500 text-sm">Loading...</div>
            ) : findings.length === 0 ? (
              <div className="px-6 py-8 text-center text-slate-500 text-sm">No open findings 🎉</div>
            ) : findings.map((f) => (
              <Link key={f.id} href={`/findings/${f.id}`} className="flex items-center justify-between px-6 py-3.5 hover:bg-white/5 transition group">
                <div className="min-w-0 mr-4">
                  <p className="text-sm text-white font-medium truncate group-hover:text-indigo-300 transition">{f.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5 truncate">{f.file_path}</p>
                </div>
                <SeverityBadge severity={f.severity} />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
