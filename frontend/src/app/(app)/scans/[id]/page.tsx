'use client';

import useSWR from 'swr';
import { scansApi, findingsApi } from '@/lib/api';
import { useParams } from 'next/navigation';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SeverityBadge } from '@/components/ui/SeverityBadge';
import { formatDate, shortSha } from '@/lib/utils';
import Link from 'next/link';
import { GitCommit, Clock, CheckCircle, AlertTriangle, ShieldAlert, ArrowLeft } from 'lucide-react';

export default function ScanDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: scan } = useSWR(`scan-${id}`, () => scansApi.get(id));
  const { data: findings } = useSWR(`scan-findings-${id}`, () => findingsApi.list({ scan_id: id, page_size: 50 }));

  const duration =
    scan?.started_at && scan?.finished_at
      ? Math.round((new Date(scan.finished_at).getTime() - new Date(scan.started_at).getTime()) / 1000)
      : null;

  return (
    <div className="space-y-6 max-w-5xl">
      <Link href="/scans" className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition w-fit">
        <ArrowLeft size={14} /> All scans
      </Link>

      {/* Header */}
      <div className="bg-[#141414] rounded-2xl border border-white/5 p-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <StatusBadge status={scan?.status ?? 'pending'} />
              {scan?.trigger && <span className="text-xs text-slate-500 capitalize">{scan.trigger}</span>}
            </div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <GitCommit size={18} className="text-slate-500" />
              {shortSha(scan?.commit_sha)} · {scan?.branch ?? 'main'}
            </h1>
            {scan?.pr_number && <p className="text-sm text-slate-400 mt-1">Pull Request #{scan.pr_number}</p>}
            {scan?.error_message && (
              <div className="mt-3 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                {scan.error_message}
              </div>
            )}
          </div>
          <div className="flex flex-col gap-1.5 text-sm text-slate-400 text-right">
            <span className="flex items-center gap-1.5 justify-end"><Clock size={13} /> {formatDate(scan?.started_at)}</span>
            {duration != null && <span className="text-xs text-slate-500">Duration: {duration}s</span>}
          </div>
        </div>

        {/* Counts */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
          {[
            { label: 'Total Findings', value: scan?.findings_count ?? 0, color: 'text-white' },
            { label: 'Critical', value: scan?.critical_count ?? 0, color: 'text-red-400' },
            { label: 'High', value: findings?.filter(f => f.severity === 'high').length ?? 0, color: 'text-orange-400' },
            { label: 'Open', value: findings?.filter(f => f.status === 'open').length ?? 0, color: 'text-yellow-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-[#080808] rounded-xl border border-white/5 px-4 py-3 text-center">
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Findings */}
      <div className="bg-[#141414] rounded-2xl border border-white/5 overflow-hidden">
        <div className="px-6 py-4 border-b border-white/5 flex items-center gap-2">
          <ShieldAlert size={15} className="text-orange-400" />
          <h2 className="font-semibold text-white">Findings ({findings?.length ?? 0})</h2>
        </div>
        <div className="divide-y divide-white/5">
          {!findings ? (
            <div className="px-6 py-10 text-center text-slate-500">Loading…</div>
          ) : findings.length === 0 ? (
            <div className="px-6 py-10 text-center text-slate-500 flex flex-col items-center gap-2">
              <CheckCircle size={28} className="text-emerald-500 opacity-60" />
              <span>No findings — clean scan!</span>
            </div>
          ) : findings.map((f) => (
            <Link key={f.id} href={`/findings/${f.id}`} className="flex items-center gap-4 px-6 py-4 hover:bg-white/[0.03] transition group">
              <SeverityBadge severity={f.severity} />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-white font-medium group-hover:text-indigo-300 transition truncate">{f.title}</p>
                <p className="text-xs text-slate-500 mt-0.5 truncate">{f.file_path}{f.line_start ? `:${f.line_start}` : ''}</p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs text-slate-500">{f.tool}</span>
                <StatusBadge status={f.status} />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
