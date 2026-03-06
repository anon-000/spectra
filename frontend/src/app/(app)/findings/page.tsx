'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { findingsApi, reposApi } from '@/lib/api';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SeverityBadge } from '@/components/ui/SeverityBadge';
import { Pagination } from '@/components/ui/Pagination';
import { useToast } from '@/components/ui/Toaster';
import { formatDateShort } from '@/lib/utils';
import Link from 'next/link';
import { ShieldAlert, Filter } from 'lucide-react';

const SEVERITIES = ['', 'critical', 'high', 'medium', 'low', 'info'];
const STATUSES = ['', 'open', 'resolved', 'suppressed', 'false_positive'];
const CATEGORIES = ['', 'sast', 'sca', 'secret', 'container', 'iac'];

export default function FindingsPage() {
  const [page, setPage] = useState(1);
  const [severity, setSeverity] = useState('');
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('open');
  const [repoId, setRepoId] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkStatus, setBulkStatus] = useState('resolved');
  const { toast } = useToast();

  const { data: repos } = useSWR('repos', () => reposApi.list());
  const { data: findings, isLoading, mutate } = useSWR(
    ['findings', severity, category, status, repoId, page],
    () => findingsApi.list({ severity: severity || undefined, category: category || undefined, status: status || undefined, repo_id: repoId || undefined, page, page_size: 20 })
  );

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };
  const selectAll = () => setSelected(new Set(findings?.map(f => f.id) ?? []));
  const clearSelect = () => setSelected(new Set());

  const bulkUpdate = async () => {
    if (selected.size === 0) return;
    try {
      await findingsApi.bulkUpdate({ finding_ids: Array.from(selected), status: bulkStatus });
      toast('success', `${selected.size} finding(s) marked as ${bulkStatus}`);
      clearSelect();
      mutate();
    } catch {
      toast('error', 'Bulk update failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-white">Findings</h1>
          <p className="text-slate-400 mt-1 text-sm">All detected security issues across your repositories</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <Filter size={15} className="text-slate-500" />
        <select value={repoId} onChange={e => { setRepoId(e.target.value); setPage(1); }}
          className="bg-[#141414] border border-white/10 text-slate-300 text-sm pl-3 pr-8 py-2 rounded-xl focus:outline-none focus:border-indigo-500 appearance-none">
          <option value="">All repos</option>
          {repos?.map(r => <option key={r.id} value={r.id}>{r.full_name}</option>)}
        </select>
        <select value={severity} onChange={e => { setSeverity(e.target.value); setPage(1); }}
          className="bg-[#141414] border border-white/10 text-slate-300 text-sm pl-3 pr-8 py-2 rounded-xl focus:outline-none focus:border-indigo-500 appearance-none">
          {SEVERITIES.map(s => <option key={s} value={s}>{s || 'All severities'}</option>)}
        </select>
        <select value={category} onChange={e => { setCategory(e.target.value); setPage(1); }}
          className="bg-[#141414] border border-white/10 text-slate-300 text-sm pl-3 pr-8 py-2 rounded-xl focus:outline-none focus:border-indigo-500 appearance-none">
          {CATEGORIES.map(c => <option key={c} value={c}>{c || 'All categories'}</option>)}
        </select>
        <select value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}
          className="bg-[#141414] border border-white/10 text-slate-300 text-sm pl-3 pr-8 py-2 rounded-xl focus:outline-none focus:border-indigo-500 appearance-none">
          {STATUSES.map(s => <option key={s} value={s}>{s || 'All statuses'}</option>)}
        </select>
      </div>

      {/* Bulk actions */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl px-4 py-3">
          <span className="text-sm text-indigo-300 font-medium">{selected.size} selected</span>
          <select value={bulkStatus} onChange={e => setBulkStatus(e.target.value)}
            className="bg-[#080808] border border-white/10 text-slate-300 text-sm px-2 py-1.5 rounded-lg focus:outline-none">
            {['resolved', 'suppressed', 'false_positive', 'open'].map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
          </select>
          <button onClick={bulkUpdate} className="px-3 py-1.5 bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-semibold rounded-lg transition">
            Apply
          </button>
          <button onClick={clearSelect} className="text-xs text-slate-400 hover:text-white ml-1 transition">Clear</button>
        </div>
      )}

      {/* Table */}
      <div className="bg-[#141414] rounded-2xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-xs text-slate-500 uppercase tracking-wide">
                <th className="px-4 py-3.5 w-8">
                  <input type="checkbox" className="rounded" onChange={e => e.target.checked ? selectAll() : clearSelect()} checked={selected.size === (findings?.length ?? 0) && selected.size > 0} />
                </th>
                <th className="px-4 py-3.5 text-left">Title</th>
                <th className="px-4 py-3.5 text-left">File</th>
                <th className="px-4 py-3.5 text-left">Severity</th>
                <th className="px-4 py-3.5 text-left">Category</th>
                <th className="px-4 py-3.5 text-left">Status</th>
                <th className="px-4 py-3.5 text-left">First seen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                [...Array(8)].map((_, i) => (
                  <tr key={i}>{[...Array(7)].map((_, j) => <td key={j} className="px-4 py-4"><div className="h-4 bg-white/5 rounded animate-pulse w-24" /></td>)}</tr>
                ))
              ) : findings?.length === 0 ? (
                <tr><td colSpan={7} className="px-6 py-16 text-center text-slate-500">
                  <ShieldAlert size={36} className="mx-auto mb-2 opacity-20" />
                  No findings match your filters
                </td></tr>
              ) : findings?.map(f => (
                <tr key={f.id} className={`hover:bg-white/[0.03] transition group ${selected.has(f.id) ? 'bg-indigo-500/5' : ''}`}>
                  <td className="px-4 py-3.5 text-center">
                    <input type="checkbox" className="rounded" checked={selected.has(f.id)} onChange={() => toggleSelect(f.id)} />
                  </td>
                  <td className="px-4 py-3.5">
                    <Link href={`/findings/${f.id}`} className="text-white group-hover:text-indigo-300 transition font-medium">
                      {f.title}
                      {f.cve_id && <span className="ml-2 text-xs text-slate-500">{f.cve_id}</span>}
                    </Link>
                    <p className="text-xs text-slate-500 mt-0.5">{f.tool} · {f.rule_id}</p>
                  </td>
                  <td className="px-4 py-3.5 text-slate-400 text-xs font-mono max-w-[180px] truncate">
                    {f.file_path}{f.line_start ? `:${f.line_start}` : ''}
                  </td>
                  <td className="px-4 py-3.5"><SeverityBadge severity={f.severity} /></td>
                  <td className="px-4 py-3.5 text-slate-400 capitalize text-xs">{f.category}</td>
                  <td className="px-4 py-3.5"><StatusBadge status={f.status} /></td>
                  <td className="px-4 py-3.5 text-slate-500 text-xs whitespace-nowrap">{formatDateShort(f.first_seen)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {findings && (
          <div className="flex justify-end px-6 py-4 border-t border-white/5">
            <Pagination page={page} pageSize={20} count={findings.length} onPage={setPage} />
          </div>
        )}
      </div>
    </div>
  );
}
