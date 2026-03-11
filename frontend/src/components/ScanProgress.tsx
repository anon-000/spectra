'use client';

import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import type { ScanProgressEvent } from '@/lib/useSSE';

const STAGE_LABELS: Record<string, string> = {
  cloning: 'Cloning Repository',
  sast_running: 'Running SAST Analysis',
  sca_running: 'Running SCA Scanner',
  secrets_running: 'Scanning for Secrets',
  license_running: 'Checking Licenses',
  normalizing: 'Normalizing Results',
  ai_triage: 'AI Triage',
  policy_eval: 'Evaluating Policies',
  completed: 'Completed',
  failed: 'Failed',
};

export function ScanProgress({ event }: { event: ScanProgressEvent | null }) {
  if (!event) return null;

  const isComplete = event.stage === 'completed';
  const isFailed = event.stage === 'failed';
  const stageLabel = STAGE_LABELS[event.stage] || event.stage;

  return (
    <div className="bg-[#141414] rounded-2xl border border-white/5 p-6 space-y-4">
      <div className="flex items-center gap-3">
        {isComplete ? (
          <CheckCircle size={20} className="text-emerald-400" />
        ) : isFailed ? (
          <XCircle size={20} className="text-red-400" />
        ) : (
          <Loader2 size={20} className="text-indigo-400 animate-spin" />
        )}
        <div>
          <p className="text-sm font-medium text-white">{stageLabel}</p>
          <p className="text-xs text-slate-500">{event.message}</p>
        </div>
        <span className="ml-auto text-sm font-mono text-slate-400">{event.progress_pct}%</span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-[#080808] rounded-full h-2 border border-white/5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${
            isFailed ? 'bg-red-500' : isComplete ? 'bg-emerald-500' : 'bg-indigo-500'
          }`}
          style={{ width: `${event.progress_pct}%` }}
        />
      </div>
    </div>
  );
}
