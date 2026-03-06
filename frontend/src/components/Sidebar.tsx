'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  GitBranch,
  ScanSearch,
  ShieldAlert,
  FileCode,
  LogOut,
  Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/auth';

const nav = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'Repositories', href: '/repos', icon: GitBranch },
  { label: 'Scans', href: '/scans', icon: ScanSearch },
  { label: 'Findings', href: '/findings', icon: ShieldAlert },
  { label: 'Policies', href: '/policies', icon: FileCode },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex flex-col w-64 min-h-screen bg-[#0f0f0f] border-r border-white/5 px-4 py-6 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-2 mb-8">
        <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
          <Zap size={16} className="text-white" />
        </div>
        <span className="text-white font-bold text-lg tracking-tight">Spectra</span>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1 flex-1">
        {nav.map(({ label, href, icon: Icon }) => {
          const active = href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
                active
                  ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              )}
            >
              <Icon size={17} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      {user && (
        <div className="mt-4 pt-4 border-t border-white/5">
          <div className="flex items-center gap-3 px-2 mb-3">
            {user.avatar_url && (
              <img src={user.avatar_url} alt={user.github_login} className="w-8 h-8 rounded-full border border-white/10" />
            )}
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.github_login}</p>
              {user.email && <p className="text-xs text-slate-500 truncate">{user.email}</p>}
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2.5 w-full px-3 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/5 transition"
          >
            <LogOut size={15} />
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
