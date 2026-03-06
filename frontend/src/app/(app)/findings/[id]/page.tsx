'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { findingsApi } from '@/lib/api';
import { useParams } from 'next/navigation';
import { SeverityBadge } from '@/components/ui/SeverityBadge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useToast } from '@/components/ui/Toaster';
import { formatDate, shortSha } from '@/lib/utils';
import Link from 'next/link';
import { ArrowLeft, Brain, Wrench, Clock, GitCommit, Package, Shield } from 'lucide-react';

const VALID_STATUSES = ['open', 'resolved', 'suppressed', 'false_positive'];

export default function FindingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: finding, mutate } = useSWR(`finding-${id}`, () => findingsApi.get(id));
  const { data: events } = useSWR(`finding-events-${id}`, () => findingsApi.events(id));
  const { toast } = useToast();
  const [updating, setUpdating] = useState(false);

  const updateStatus = async (status: string) => {
    setUpdating(true);
    try {
      await findingsApi.update(id, { status });
      await mutate();
      toast('success', `Status updated to ${status}`);
    } catch {
      toast('error', 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="max-w-4xl space-y-6">
      <Link href="/findings" className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition w-fit">
        <ArrowLeft size={14} /> All findings
      </Link>

      {/* Header */}
      <div className="bg-[#141414] rounded-2xl border border-white/5 p-6">
        <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
          <div className="flex items-center gap-2 flex-wrap">
            <SeverityBadge severity={finding?.severity ?? 'info'} />
            <StatusBadge status={finding?.status ?? 'open'} />
            {finding?.ai_severity && finding.ai_severity !== finding.severity && (
              <span className="flex items-center gap-1 text-xs text-purple-400 bg-purple-500/10 border border-purple-500/20 rounded-full px-2 py-0.5">
                <Brain size={10} /> AI: {finding.ai_severity}
              </span>
            )}
          </div>
          {/* Status update */}
          <select
            value={finding?.status}
            disabled={updating}
            onChange={e => updateStatus(e.target.value)}
            className="bg-[#080808] border border-white/10 text-slate-300 text-sm px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500 disabled:opacity-50"
          >
            {VALID_STATUSES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
          </select>
        </div>

        <h1 className="text-xl font-bold text-white mb-2">{finding?.title}</h1>
        {finding?.description && <p className="text-slate-400 text-sm leading-relaxed mb-4">{finding.description}</p>}

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-slate-400">
          <div><span className="text-slate-600 block mb-0.5">Tool</span>{finding?.tool}</div>
          <div><span className="text-slate-600 block mb-0.5">Rule</span>{finding?.rule_id}</div>
          <div><span className="text-slate-600 block mb-0.5">Category</span>{finding?.category}</div>
          <div><span className="text-slate-600 block mb-0.5">Confidence</span>{finding?.confidence != null ? `${(finding.confidence * 100).toFixed(0)}%` : '—'}</div>
        </div>
      </div>

      {/* Location */}
      <div className="bg-[#141414] rounded-2xl border border-white/5 p-6 space-y-3">
        <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2"><GitCommit size={14} /> Location</h2>
        <p className="font-mono text-sm text-indigo-300 bg-[#080808] rounded-lg px-4 py-2.5 border border-white/5">
          {finding?.file_path}{finding?.line_start ? `:${finding.line_start}` : ''}
          {finding?.line_end && finding.line_end !== finding.line_start ? `–${finding.line_end}` : ''}
        </p>
        {finding?.snippet && (
          <pre className="text-xs text-slate-300 bg-[#080808] rounded-lg px-4 py-3 border border-white/5 overflow-x-auto leading-relaxed">
            <code>{finding.snippet}</code>
          </pre>
        )}
        <div className="flex gap-4 text-xs text-slate-500">
          {finding?.commit_sha && <span className="flex items-center gap-1"><GitCommit size={11} />{shortSha(finding.commit_sha)}</span>}
          <span className="flex items-center gap-1"><Clock size={11} />First seen {formatDate(finding?.first_seen)}</span>
        </div>
      </div>

      {/* Vulnerability / Package info */}
      {(finding?.cve_id || finding?.cwe_id || finding?.package_name) && (
        <div className="bg-[#141414] rounded-2xl border border-white/5 p-6 space-y-3">
          <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2"><Package size={14} /> Vulnerability Info</h2>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {finding?.cve_id && <div><span className="text-slate-600 text-xs block">CVE</span><span className="text-red-400 font-mono">{finding.cve_id}</span></div>}
            {finding?.cwe_id && <div><span className="text-slate-600 text-xs block">CWE</span><span className="text-orange-400 font-mono">{finding.cwe_id}</span></div>}
            {finding?.package_name && <div><span className="text-slate-600 text-xs block">Package</span><span className="text-white font-mono">{finding.package_name}</span></div>}
            {finding?.package_version && <div><span className="text-slate-600 text-xs block">Version</span><span className="text-white font-mono">{finding.package_version}</span></div>}
          </div>
        </div>
      )}

      {/* AI Analysis */}
      {(finding?.ai_explanation || finding?.ai_suggested_fix || finding?.ai_verdict) && (
        <div className="bg-gradient-to-br from-purple-500/5 to-indigo-500/5 rounded-2xl border border-purple-500/15 p-6 space-y-4">
          <h2 className="text-sm font-semibold text-purple-300 flex items-center gap-2"><Brain size={14} /> AI Analysis</h2>
          {finding?.ai_verdict && (
            <div className="inline-flex items-center gap-1.5 text-xs bg-purple-500/15 text-purple-300 border border-purple-500/20 rounded-full px-3 py-1">
              <Shield size={11} /> Verdict: {finding.ai_verdict}
            </div>
          )}
          {finding?.ai_explanation && (
            <div>
              <p className="text-xs text-slate-500 mb-1.5">Explanation</p>
              <p className="text-sm text-slate-300 leading-relaxed">{finding.ai_explanation}</p>
            </div>
          )}
          {finding?.ai_suggested_fix && (
            <div>
              <p className="text-xs text-slate-500 mb-1.5 flex items-center gap-1"><Wrench size={10} /> Suggested Fix</p>
              <pre className="text-xs text-emerald-300 bg-[#080808] rounded-lg px-4 py-3 border border-emerald-500/10 overflow-x-auto leading-relaxed whitespace-pre-wrap">
                {finding.ai_suggested_fix}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Event History */}
      <div className="bg-[#141414] rounded-2xl border border-white/5 overflow-hidden">
        <div className="px-6 py-4 border-b border-white/5">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2"><Clock size={14} /> Event History</h2>
        </div>
        <div className="divide-y divide-white/5">
          {!events || events.length === 0 ? (
            <div className="px-6 py-8 text-center text-slate-500 text-sm">No events yet</div>
          ) : events.map(ev => (
            <div key={ev.id} className="px-6 py-3.5 flex items-center gap-4 text-sm">
              <span className="text-slate-600 text-xs w-36 shrink-0">{formatDate(ev.created_at)}</span>
              <span className="text-slate-300 capitalize">{ev.action.replace('_', ' ')}</span>
              {ev.old_value && ev.new_value && (
                <span className="text-xs text-slate-500">
                  <span className="text-red-400">{ev.old_value}</span>
                  {' → '}
                  <span className="text-emerald-400">{ev.new_value}</span>
                </span>
              )}
              {ev.comment && <span className="text-slate-500 italic text-xs">{ev.comment}</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
