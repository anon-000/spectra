'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { analyticsApi, reposApi } from '@/lib/api';
import { FindingsOverTimeChart } from '@/components/charts/FindingsOverTimeChart';
import { SeverityChart } from '@/components/charts/SeverityChart';
import { CategoryChart } from '@/components/charts/CategoryChart';
import { MTTRChart } from '@/components/charts/MTTRChart';
import { ShieldAlert, CheckCircle, EyeOff, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

const PERIODS = [
  { label: '30 days', value: '30d' },
  { label: '90 days', value: '90d' },
  { label: '1 year', value: '1y' },
];

function StatCard({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: string | number; color: string }) {
  return (
    <div className="bg-[#141414] rounded-2xl border border-white/5 p-5 flex items-center gap-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
        <Icon size={18} className="text-white" />
      </div>
      <div>
        <p className="text-slate-400 text-xs">{label}</p>
        <p className="text-xl font-bold text-white mt-0.5">{value}</p>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState('30d');
  const [repoId, setRepoId] = useState<string>('');

  const { data: repos } = useSWR('repos', () => reposApi.list());
  const { data, isLoading } = useSWR(
    `analytics-${period}-${repoId}`,
    () => analyticsApi.trends({ period, repo_id: repoId || undefined }),
  );

  const avgMTTR = data?.mttr_by_severity?.length
    ? (data.mttr_by_severity.reduce((sum, m) => sum + m.avg_hours, 0) / data.mttr_by_severity.length).toFixed(1)
    : '—';

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
          <p className="text-slate-400 mt-1 text-sm">Finding trends and security metrics</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Repo filter */}
          <select
            value={repoId}
            onChange={e => setRepoId(e.target.value)}
            className="bg-[#141414] border border-white/10 text-slate-300 text-sm px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500"
          >
            <option value="">All repositories</option>
            {repos?.map(r => (
              <option key={r.id} value={r.id}>{r.full_name}</option>
            ))}
          </select>

          {/* Period tabs */}
          <div className="flex bg-[#141414] border border-white/10 rounded-xl overflow-hidden">
            {PERIODS.map(p => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={cn(
                  'px-3 py-2 text-sm font-medium transition',
                  period === p.value
                    ? 'bg-indigo-500/20 text-indigo-300'
                    : 'text-slate-400 hover:text-white hover:bg-white/5',
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center text-slate-500 py-20">Loading analytics…</div>
      ) : data ? (
        <>
          {/* Summary stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard icon={ShieldAlert} label="Open Findings" value={data.total_open} color="bg-orange-500/80" />
            <StatCard icon={CheckCircle} label="Resolved" value={data.total_resolved} color="bg-emerald-500/80" />
            <StatCard icon={EyeOff} label="Suppressed" value={data.total_suppressed} color="bg-slate-500/80" />
            <StatCard icon={Clock} label="Avg MTTR" value={`${avgMTTR}h`} color="bg-indigo-500/80" />
          </div>

          {/* Charts */}
          <FindingsOverTimeChart data={data.time_series} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SeverityChart data={data.by_severity} />
            <CategoryChart data={data.by_category} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MTTRChart data={data.mttr_by_severity} />

            {/* Top Rules */}
            <div className="bg-[#141414] rounded-2xl border border-white/5 p-6">
              <h3 className="text-sm font-semibold text-white mb-4">Top Rules</h3>
              <div className="space-y-2">
                {data.top_rules.length === 0 ? (
                  <p className="text-slate-500 text-sm">No data</p>
                ) : data.top_rules.map((rule, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <div className="min-w-0">
                      <p className="text-slate-300 truncate font-mono text-xs">{rule.rule_id}</p>
                      <p className="text-slate-600 text-xs">{rule.tool}</p>
                    </div>
                    <span className="text-white font-medium ml-3 shrink-0">{rule.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Top Repos */}
          {!repoId && data.top_repos.length > 0 && (
            <div className="bg-[#141414] rounded-2xl border border-white/5 p-6">
              <h3 className="text-sm font-semibold text-white mb-4">Top Repositories by Open Findings</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {data.top_repos.map((repo, i) => (
                  <div key={i} className="flex items-center justify-between text-sm bg-[#080808] rounded-xl px-4 py-3 border border-white/5">
                    <span className="text-slate-300 truncate font-mono text-xs">{repo.full_name}</span>
                    <span className="text-white font-medium ml-3 shrink-0">{repo.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
