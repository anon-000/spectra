'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend, type PieLabelRenderProps } from 'recharts';
import type { CategoryCount } from '@/types';

const COLORS: Record<string, string> = {
  sast: '#6366f1',
  sca: '#f97316',
  secret: '#ef4444',
  license: '#22c55e',
};

export function CategoryChart({ data }: { data: CategoryCount[] }) {
  return (
    <div className="bg-[#141414] rounded-2xl border border-white/5 p-6">
      <h3 className="text-sm font-semibold text-white mb-4">By Category</h3>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="category"
            cx="50%"
            cy="50%"
            outerRadius={80}
            innerRadius={40}
            strokeWidth={0}
            label={(props: PieLabelRenderProps) => `${props.name || ''} ${((props.percent ?? 0) * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {data.map((entry) => (
              <Cell key={entry.category} fill={COLORS[entry.category] || '#64748b'} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, fontSize: 12 }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
