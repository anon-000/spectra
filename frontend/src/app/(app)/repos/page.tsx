'use client';

import useSWR from 'swr';
import { reposApi } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toaster';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { formatDate } from '@/lib/utils';
import Link from 'next/link';
import { GitBranch, Code2, ToggleLeft, ToggleRight, ExternalLink, RefreshCw } from 'lucide-react';
import { useState, useMemo, useEffect } from 'react';

export default function ReposPage() {
  const { data: repos, mutate, isLoading } = useSWR('repos', () => reposApi.list());
  const { toast } = useToast();
  const { user } = useAuth();
  const [syncing, setSyncing] = useState(false);
  const [activeEntity, setActiveEntity] = useState<string | null>(null);

  // Group repos by entity (owner/org prefix of full_name), current user first
  const entities = useMemo(() => {
    if (!repos) return [];
    const set = new Set(repos.map((r) => r.full_name.split('/')[0]));
    const sorted = Array.from(set).sort();
    const login = user?.github_login;
    if (login && sorted.includes(login)) {
      return [login, ...sorted.filter((e) => e !== login)];
    }
    return sorted;
  }, [repos, user]);

  // Auto-select first entity when repos load
  useEffect(() => {
    if (entities.length > 0 && !activeEntity) {
      setActiveEntity(entities[0]);
    }
  }, [entities, activeEntity]);

  const filteredRepos = useMemo(() => {
    if (!repos || !activeEntity) return [];
    return repos.filter((r) => r.full_name.startsWith(activeEntity + '/'));
  }, [repos, activeEntity]);

  const toggleActive = async (id: string, current: boolean) => {
    try {
      await reposApi.update(id, { is_active: !current });
      await mutate();
      toast('success', `Repository ${current ? 'disabled' : 'enabled'}`);
    } catch {
      toast('error', 'Failed to update repository');
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await reposApi.sync();
      await mutate();
      toast('success', 'Repositories synced from GitHub');
    } catch {
      toast('error', 'Failed to sync repositories');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Repositories</h1>
          <p className="text-slate-400 mt-1 text-sm">Manage which repositories Spectra monitors</p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-500 transition disabled:opacity-50"
        >
          <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
          {syncing ? 'Syncing...' : 'Sync Repos'}
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-36 bg-[#141414] rounded-2xl border border-white/5 animate-pulse" />
          ))}
        </div>
      ) : repos?.length === 0 ? (
        <div className="text-center py-24 text-slate-500">
          <GitBranch size={40} className="mx-auto mb-3 opacity-30" />
          <p>No repositories connected yet.</p>
          <p className="text-sm mt-1">Install the Spectra GitHub App to get started.</p>
        </div>
      ) : (
        <>
          {/* Entity tabs */}
          <div className="relative">
            <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
            {entities.map((entity) => {
              const count = repos?.filter((r) => r.full_name.startsWith(entity + '/')).length ?? 0;
              return (
                <button
                  key={entity}
                  onClick={() => setActiveEntity(entity)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition ${
                    activeEntity === entity
                      ? 'bg-indigo-600 text-white'
                      : 'bg-[#141414] text-slate-400 hover:text-white border border-white/5 hover:border-white/10'
                  }`}
                >
                  {entity}{entity === user?.github_login ? ' (You)' : ''}
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                    activeEntity === entity ? 'bg-indigo-500 text-white' : 'bg-white/5 text-slate-500'
                  }`}>
                    {count}
                  </span>
                </button>
              );
            })}
            </div>
            {/* Right fade */}
            <div className="pointer-events-none absolute right-0 top-0 h-full w-16 bg-gradient-to-l from-[#080808] to-transparent" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredRepos.map((repo) => (
            <div key={repo.id} className="bg-[#141414] rounded-2xl border border-white/5 p-5 flex flex-col gap-4 hover:border-white/10 transition">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <Link href={`/repos/${repo.id}`} className="font-semibold text-white hover:text-indigo-300 transition text-sm truncate block">
                    {repo.full_name.split('/').slice(1).join('/')}
                  </Link>
                  <div className="flex items-center gap-2 mt-1">
                    {repo.language && (
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        <Code2 size={11} /> {repo.language}
                      </span>
                    )}
                    <span className="text-xs text-slate-600">· {repo.default_branch}</span>
                  </div>
                </div>
                <button
                  onClick={() => toggleActive(repo.id, repo.is_active)}
                  className="shrink-0 text-slate-400 hover:text-indigo-400 transition"
                  title={repo.is_active ? 'Disable monitoring' : 'Enable monitoring'}
                >
                  {repo.is_active ? <ToggleRight size={24} className="text-indigo-400" /> : <ToggleLeft size={24} />}
                </button>
              </div>

              <div className="flex items-center justify-between">
                <StatusBadge status={repo.is_active ? 'completed' : 'suppressed'} />
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-500">{formatDate(repo.updated_at)}</span>
                  <Link href={`/repos/${repo.id}`} className="text-slate-500 hover:text-indigo-400 transition">
                    <ExternalLink size={13} />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
        </>
      )}
    </div>
  );
}
