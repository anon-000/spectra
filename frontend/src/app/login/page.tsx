'use client';

import { Github, Zap } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function LoginPage() {
  const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;
  const [githubUrl, setGithubUrl] = useState('');

  useEffect(() => {
    const redirectUri = `${window.location.origin}/auth/callback`;
    setGithubUrl(`https://github.com/login/oauth/authorize?client_id=${clientId}&scope=read:user,user:email,repo,read:org&redirect_uri=${encodeURIComponent(redirectUri)}`);
  }, [clientId]);

  return (
    <div className="min-h-screen bg-[#080808] flex items-center justify-center relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-2/3 right-1/4 w-[300px] h-[300px] bg-purple-600/8 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 w-full max-w-sm px-6">
        {/* Logo */}
        <div className="flex flex-col items-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500 flex items-center justify-center shadow-2xl shadow-indigo-500/30 mb-4">
            <Zap size={30} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Spectra</h1>
          <p className="text-slate-400 mt-2 text-sm text-center">Security Intelligence Platform<br />for your GitHub repositories</p>
        </div>

        {/* Card */}
        <div className="bg-[#141414] rounded-2xl border border-white/8 p-8 shadow-2xl">
          <h2 className="text-lg font-semibold text-white mb-1">Welcome back</h2>
          <p className="text-slate-400 text-sm mb-6">Sign in with your GitHub account to get started.</p>

          <a
            href={githubUrl || '#'}
            className="flex items-center justify-center gap-3 w-full py-3 px-4 rounded-xl bg-white text-gray-900 font-semibold text-sm hover:bg-gray-100 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg"
          >
            <Github size={18} />
            Continue with GitHub
          </a>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          By signing in you agree to our terms of service and privacy policy.
        </p>
      </div>
    </div>
  );
}
