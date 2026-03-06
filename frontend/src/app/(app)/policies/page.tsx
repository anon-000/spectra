'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { policiesApi } from '@/lib/api';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useToast } from '@/components/ui/Toaster';
import { formatDate } from '@/lib/utils';
import { FileCode, Plus, Pencil, Trash2, Loader2 } from 'lucide-react';
import type { Policy, PolicyRules } from '@/types';

const defaultRules = (): PolicyRules => ({
  fail_on: [],
  max_critical: null,
  max_high: null,
  block_licenses: [],
});

function PolicyForm({ initial, onSave, onClose }: {
  initial?: Policy;
  onSave: (name: string, rules: PolicyRules) => Promise<void>;
  onClose: () => void;
}) {
  const [name, setName] = useState(initial?.name ?? '');
  const [failOn, setFailOn] = useState<string[]>(initial?.rules?.fail_on ?? []);
  const [maxCritical, setMaxCritical] = useState<string>(initial?.rules?.max_critical?.toString() ?? '');
  const [maxHigh, setMaxHigh] = useState<string>(initial?.rules?.max_high?.toString() ?? '');
  const [blockLicenses, setBlockLicenses] = useState<string>(initial?.rules?.block_licenses?.join(', ') ?? '');
  const [loading, setLoading] = useState(false);

  const SEVERITIES = ['critical', 'high', 'medium', 'low'];
  const toggleFail = (s: string) => setFailOn(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const rules: PolicyRules = {
        fail_on: failOn,
        max_critical: maxCritical !== '' ? parseInt(maxCritical) : null,
        max_high: maxHigh !== '' ? parseInt(maxHigh) : null,
        block_licenses: blockLicenses ? blockLicenses.split(',').map(s => s.trim()).filter(Boolean) : [],
      };
      await onSave(name, rules);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-5">
      <div>
        <label className="block text-xs text-slate-400 mb-1.5 font-medium">Policy Name <span className="text-red-400">*</span></label>
        <input required value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Production Gate"
          className="w-full bg-[#080808] border border-white/10 text-white text-sm px-3 py-2.5 rounded-xl focus:outline-none focus:border-indigo-500 transition" />
      </div>

      <div>
        <label className="block text-xs text-slate-400 mb-2 font-medium">Fail on severities</label>
        <div className="flex flex-wrap gap-2">
          {SEVERITIES.map(s => (
            <button key={s} type="button" onClick={() => toggleFail(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${failOn.includes(s) ? 'bg-indigo-500 text-white' : 'bg-white/5 text-slate-400 hover:bg-white/10'}`}>
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1.5 font-medium">Max Critical</label>
          <input type="number" min="0" value={maxCritical} onChange={e => setMaxCritical(e.target.value)} placeholder="∞"
            className="w-full bg-[#080808] border border-white/10 text-white text-sm px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500" />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1.5 font-medium">Max High</label>
          <input type="number" min="0" value={maxHigh} onChange={e => setMaxHigh(e.target.value)} placeholder="∞"
            className="w-full bg-[#080808] border border-white/10 text-white text-sm px-3 py-2 rounded-xl focus:outline-none focus:border-indigo-500" />
        </div>
      </div>

      <div>
        <label className="block text-xs text-slate-400 mb-1.5 font-medium">Block Licenses <span className="text-slate-600">(comma-separated)</span></label>
        <input value={blockLicenses} onChange={e => setBlockLicenses(e.target.value)} placeholder="e.g. GPL-3.0, AGPL-3.0"
          className="w-full bg-[#080808] border border-white/10 text-white text-sm px-3 py-2.5 rounded-xl focus:outline-none focus:border-indigo-500" />
      </div>

      <div className="flex justify-end gap-3 pt-1">
        <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/5 transition">Cancel</button>
        <button type="submit" disabled={loading}
          className="flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-semibold transition disabled:opacity-60">
          {loading && <Loader2 size={14} className="animate-spin" />}
          {initial ? 'Update Policy' : 'Create Policy'}
        </button>
      </div>
    </form>
  );
}

export default function PoliciesPage() {
  const { data: policies, isLoading, mutate } = useSWR('policies', () => policiesApi.list());
  const { toast } = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [editPolicy, setEditPolicy] = useState<Policy | null>(null);

  const handleCreate = async (name: string, rules: PolicyRules) => {
    try {
      await policiesApi.create({ name, rules });
      await mutate();
      toast('success', 'Policy created');
      setCreateOpen(false);
    } catch { toast('error', 'Failed to create policy'); }
  };

  const handleUpdate = async (name: string, rules: PolicyRules) => {
    if (!editPolicy) return;
    try {
      await policiesApi.update(editPolicy.id, { name, rules });
      await mutate();
      toast('success', 'Policy updated');
      setEditPolicy(null);
    } catch { toast('error', 'Failed to update policy'); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this policy?')) return;
    try {
      await policiesApi.delete(id);
      await mutate();
      toast('success', 'Policy deleted');
    } catch { toast('error', 'Failed to delete policy'); }
  };

  const handleToggle = async (p: Policy) => {
    try {
      await policiesApi.update(p.id, { is_active: !p.is_active });
      await mutate();
      toast('success', `Policy ${p.is_active ? 'disabled' : 'enabled'}`);
    } catch { toast('error', 'Failed to update policy'); }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Policies</h1>
          <p className="text-slate-400 mt-1 text-sm">Define rules that gate your CI/CD pipeline</p>
        </div>
        <button onClick={() => setCreateOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-semibold transition-all hover:scale-[1.02] shadow-lg shadow-indigo-500/20">
          <Plus size={15} /> New Policy
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="h-28 bg-[#141414] rounded-2xl border border-white/5 animate-pulse" />)}</div>
      ) : policies?.length === 0 ? (
        <div className="text-center py-24 text-slate-500">
          <FileCode size={40} className="mx-auto mb-3 opacity-30" />
          <p>No policies yet. Create one to enforce security gates.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {policies?.map(p => (
            <div key={p.id} className="bg-[#141414] rounded-2xl border border-white/5 p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2.5 mb-1">
                    <h3 className="font-semibold text-white">{p.name}</h3>
                    <StatusBadge status={p.is_active ? 'completed' : 'suppressed'} />
                  </div>
                  <div className="flex flex-wrap gap-3 text-xs text-slate-500 mt-2">
                    {p.rules.fail_on?.length > 0 && <span>Fail on: <span className="text-orange-400">{p.rules.fail_on.join(', ')}</span></span>}
                    {p.rules.max_critical != null && <span>Max critical: <span className="text-red-400">{p.rules.max_critical}</span></span>}
                    {p.rules.max_high != null && <span>Max high: <span className="text-orange-400">{p.rules.max_high}</span></span>}
                    {p.rules.block_licenses?.length > 0 && <span>Blocked licenses: <span className="text-yellow-400">{p.rules.block_licenses.join(', ')}</span></span>}
                  </div>
                  <p className="text-xs text-slate-600 mt-2">{formatDate(p.updated_at)}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button onClick={() => handleToggle(p)} className="text-xs px-2.5 py-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition">
                    {p.is_active ? 'Disable' : 'Enable'}
                  </button>
                  <button onClick={() => setEditPolicy(p)} className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition"><Pencil size={14} /></button>
                  <button onClick={() => handleDelete(p.id)} className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition"><Trash2 size={14} /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="New Policy">
        <PolicyForm onSave={handleCreate} onClose={() => setCreateOpen(false)} />
      </Modal>

      <Modal open={!!editPolicy} onClose={() => setEditPolicy(null)} title="Edit Policy">
        {editPolicy && <PolicyForm initial={editPolicy} onSave={handleUpdate} onClose={() => setEditPolicy(null)} />}
      </Modal>
    </div>
  );
}
