'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { scansApi } from '@/lib/api';
import { useToast } from '@/components/ui/Toaster';
import { Loader2 } from 'lucide-react';

interface Props {
  open: boolean;
  onClose: () => void;
  repoId: string;
  defaultBranch: string;
  onDone?: () => void;
}

export function ManualScanModal({ open, onClose, repoId, defaultBranch, onDone }: Props) {
  const [commitSha, setCommitSha] = useState('');
  const [branch, setBranch] = useState(defaultBranch);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commitSha.trim()) { toast('error', 'Commit SHA is required'); return; }
    setLoading(true);
    try {
      await scansApi.trigger({ repo_id: repoId, commit_sha: commitSha.trim(), branch: branch.trim() || defaultBranch });
      toast('success', 'Scan queued successfully!');
      onDone?.();
      onClose();
      setCommitSha('');
    } catch {
      toast('error', 'Failed to trigger scan');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Trigger Manual Scan">
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-xs text-slate-400 mb-1.5 font-medium">Commit SHA <span className="text-red-400">*</span></label>
          <input
            value={commitSha}
            onChange={e => setCommitSha(e.target.value)}
            placeholder="e.g. a1b2c3d4e5f6..."
            className="w-full bg-[#080808] border border-white/10 text-white text-sm px-3 py-2.5 rounded-xl focus:outline-none focus:border-indigo-500 transition placeholder:text-slate-600"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1.5 font-medium">Branch</label>
          <input
            value={branch}
            onChange={e => setBranch(e.target.value)}
            placeholder={defaultBranch}
            className="w-full bg-[#080808] border border-white/10 text-white text-sm px-3 py-2.5 rounded-xl focus:outline-none focus:border-indigo-500 transition placeholder:text-slate-600"
          />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/5 transition">
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-semibold transition disabled:opacity-60"
          >
            {loading && <Loader2 size={14} className="animate-spin" />}
            {loading ? 'Queuing…' : 'Run Scan'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
