'use client';

import { cn } from '@/lib/utils';
import type { Severity } from '@/types';

const map: Record<string, string> = {
  critical: 'bg-red-500/15 text-red-400 border border-red-500/30',
  high:     'bg-orange-500/15 text-orange-400 border border-orange-500/30',
  medium:   'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
  low:      'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  info:     'bg-slate-500/15 text-slate-400 border border-slate-500/30',
};

export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide', map[severity] || map.info)}>
      {severity}
    </span>
  );
}
