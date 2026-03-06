'use client';

import { Suspense, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { authApi } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { Loader2 } from 'lucide-react';

function CallbackInner() {
  const params = useSearchParams();
  const router = useRouter();
  const { setAuth } = useAuth();

  useEffect(() => {
    const code = params.get('code');
    if (!code) { router.replace('/login'); return; }

    authApi.githubCallback(code)
      .then((data) => {
        setAuth(data.access_token, data.user);
        router.replace('/');
      })
      .catch(() => router.replace('/login'));
  }, [params, router, setAuth]);

  return (
    <div className="min-h-screen bg-[#080808] flex flex-col items-center justify-center gap-4">
      <Loader2 className="animate-spin text-indigo-400" size={36} />
      <p className="text-slate-400 text-sm">Signing you in…</p>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#080808] flex items-center justify-center">
        <Loader2 className="animate-spin text-indigo-400" size={36} />
      </div>
    }>
      <CallbackInner />
    </Suspense>
  );
}
