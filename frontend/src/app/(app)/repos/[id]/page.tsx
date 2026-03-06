'use client';

import useSWR from 'swr';
import { reposApi, scansApi } from '@/lib/api';
import { useParams } from 'next/navigation';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { formatDate, shortSha } from '@/lib/utils';
import Link from 'next/link';
import { ScanSearch, AlertTriangle, CheckCircle, GitCommit } from 'lucide-react';
import { ManualScanModal } from '@/components/ManualScanModal';
import { useState } from 'react';

export default function RepoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: repo } = useSWR(`repo-${id}`, () => reposApi.get(id));
  const { data: scans, mutate } = useSWR(`scans-repo-${id}`, () => scansApi.list({ repo_id: id, page_size: 20 }));
  const [scanOpen, setScanOpen] = useState(false);

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500 mb-1">Repository</p>
          <h1 className="text-2xl font-bold text-white">{repo?.full_name ?? '—'}</h1>
          {repo && (
            <div className="flex items-center gap-3 mt-2 text-sm text-slate-400">
              <span>{repo.language ?? 'Unknown language'}</span>
              <span>·</span>
              <span>Default branch: {repo.default_branch}</span>
            </div>
          )}
        </div>
        <button
          onClick={() => setScanOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-indigo-500/20"
        >
          <ScanSearch size={15} />
          Trigger Scan
        </button>
      </div>

      {/* Stats row */}
      {scans && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-[#141414] rounded-xl border border-white/5 p-4 text-center">
            <p className="text-3xl font-bold text-white">{scans.length}</p>
            <p className="text-xs text-slate-500 mt-1">Total scans</p>
          </div>
          <div className="bg-[#141414] rounded-xl border border-white/5 p-4 text-center">
            <p className="text-3xl font-bold text-emerald-400">{scans.filter(s => s.status === 'completed').length}</p>
            <p className="text-xs text-slate-500 mt-1">Completed</p>
          </div>
          <div className="bg-[#141414] rounded-xl border border-white/5 p-4 text-center">
            <p className="text-3xl font-bold text-red-400">{scans.reduce((a, s) => a + s.critical_count, 0)}</p>
            <p className="text-xs text-slate-500 mt-1">Critical findings</p>
          </div>
        </div>
      )}

      {/* Scans list */}
      <div className="bg-[#141414] rounded-2xl border border-white/5 overflow-hidden">
        <div className="px-6 py-4 border-b border-white/5">
          <h2 className="font-semibold text-white flex items-center gap-2"><ScanSearch size={15} className="text-indigo-400" /> Scan History</h2>
        </div>
        <div className="divide-y divide-white/5">
          {!scans ? (
            <div className="px-6 py-10 text-center text-slate-500 text-sm">Loading…</div>
          ) : scans.length === 0 ? (
            <div className="px-6 py-10 text-center text-slate-500 text-sm">No scans yet. Trigger one above.</div>
          ) : scans.map((s) => (
            <Link key={s.id} href={`/scans/${s.id}`} className="flex items-center justify-between px-6 py-4 hover:bg-white/5 transition group">
              <div className="flex items-center gap-3">
                <GitCommit size={15} className="text-slate-600" />
                <div>
                  <p className="text-sm text-white font-medium group-hover:text-indigo-300 transition">
                    {shortSha(s.commit_sha)} · {s.branch ?? 'main'}
                    {s.pr_number && <span className="ml-2 text-xs text-slate-500">PR #{s.pr_number}</span>}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">{formatDate(s.created_at)} · {s.trigger}</p>
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="flex items-center gap-1 text-red-400"><AlertTriangle size={13} /> {s.critical_count}</span>
                <span className="flex items-center gap-1 text-orange-400"><CheckCircle size={13} /> {s.findings_count}</span>
                <StatusBadge status={s.status} />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {repo && (
        <ManualScanModal
          open={scanOpen}
          onClose={() => setScanOpen(false)}
          repoId={repo.id}
          defaultBranch={repo.default_branch}
          onDone={() => mutate()}
        />
      )}
    </div>
  );
}
