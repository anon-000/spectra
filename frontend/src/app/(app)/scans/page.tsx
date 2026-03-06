'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { scansApi } from '@/lib/api';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Pagination } from '@/components/ui/Pagination';
import { formatDate, shortSha } from '@/lib/utils';
import Link from 'next/link';
import { GitCommit, AlertTriangle, ShieldAlert } from 'lucide-react';

const STATUSES = ['', 'pending', 'running', 'completed', 'failed'];

export default function ScansPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');

  const { data: scans, isLoading } = useSWR(
    ['scans', status, page],
    () => scansApi.list({ status: status || undefined, page, page_size: 20 })
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Scans</h1>
          <p className="text-slate-400 mt-1 text-sm">All repository security scans</p>
        </div>
        {/* Filter */}
        <select
          value={status}
          onChange={e => { setStatus(e.target.value); setPage(1); }}
          className="bg-[#141414] border border-white/10 text-slate-300 text-sm px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500"
        >
          {STATUSES.map(s => <option key={s} value={s}>{s || 'All statuses'}</option>)}
        </select>
      </div>

      <div className="bg-[#141414] rounded-2xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-xs text-slate-500 uppercase tracking-wide">
                <th className="px-6 py-3.5 text-left">Commit / Branch</th>
                <th className="px-6 py-3.5 text-left">Trigger</th>
                <th className="px-6 py-3.5 text-left">Findings</th>
                <th className="px-6 py-3.5 text-left">Status</th>
                <th className="px-6 py-3.5 text-left">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                [...Array(8)].map((_, i) => (
                  <tr key={i}>
                    {[...Array(5)].map((_, j) => (
                      <td key={j} className="px-6 py-4">
                        <div className="h-4 bg-white/5 rounded animate-pulse w-24" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : scans?.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-16 text-center text-slate-500">No scans found</td></tr>
              ) : scans?.map((s) => (
                <tr key={s.id} className="hover:bg-white/[0.03] transition group">
                  <td className="px-6 py-4">
                    <Link href={`/scans/${s.id}`} className="group-hover:text-indigo-300 transition font-medium text-white">
                      <span className="flex items-center gap-2">
                        <GitCommit size={13} className="text-slate-500" />
                        {shortSha(s.commit_sha)}
                      </span>
                      <span className="text-xs text-slate-500 mt-0.5 block pl-5">{s.branch ?? '—'}{s.pr_number ? ` · PR #${s.pr_number}` : ''}</span>
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-slate-400 capitalize">{s.trigger}</td>
                  <td className="px-6 py-4">
                    <span className="flex items-center gap-3 text-sm">
                      <span className="flex items-center gap-1 text-red-400"><AlertTriangle size={12} /> {s.critical_count}</span>
                      <span className="flex items-center gap-1 text-slate-400"><ShieldAlert size={12} /> {s.findings_count}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4"><StatusBadge status={s.status} /></td>
                  <td className="px-6 py-4 text-slate-500 text-xs">{formatDate(s.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {scans && (
          <div className="flex justify-end px-6 py-4 border-t border-white/5">
            <Pagination page={page} pageSize={20} count={scans.length} onPage={setPage} />
          </div>
        )}
      </div>
    </div>
  );
}
