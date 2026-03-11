'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { MTTRBySeverity } from '@/types';

const COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
};

export function MTTRChart({ data }: { data: MTTRBySeverity[] }) {
  const sorted = [...data].sort((a, b) => {
    const order = ['critical', 'high', 'medium', 'low'];
    return order.indexOf(a.severity) - order.indexOf(b.severity);
  });

  return (
    <div className="bg-[#141414] rounded-2xl border border-white/5 p-6">
      <h3 className="text-sm font-semibold text-white mb-4">Mean Time to Resolve (hours)</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={sorted} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
          <XAxis dataKey="severity" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, fontSize: 12 }}
            formatter={(value) => [`${Number(value).toFixed(1)}h`, 'Avg MTTR']}
          />
          <Bar dataKey="avg_hours" radius={[6, 6, 0, 0]} barSize={40}>
            {sorted.map((entry) => (
              <Cell key={entry.severity} fill={COLORS[entry.severity] || '#6366f1'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
