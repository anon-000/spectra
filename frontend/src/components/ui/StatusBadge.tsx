'use client';

import { cn } from '@/lib/utils';

const scanMap: Record<string, string> = {
  pending:   'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
  running:   'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  completed: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
  failed:    'bg-red-500/15 text-red-400 border border-red-500/30',
  // finding statuses
  open:           'bg-red-500/15 text-red-400 border border-red-500/30',
  resolved:       'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
  suppressed:     'bg-slate-500/15 text-slate-400 border border-slate-500/30',
  false_positive: 'bg-purple-500/15 text-purple-400 border border-purple-500/30',
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-semibold capitalize', scanMap[status] || 'bg-slate-500/15 text-slate-400')}>
      {status.replace('_', ' ')}
    </span>
  );
}
