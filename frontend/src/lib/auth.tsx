'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import type { User } from '@/types';

interface AuthCtx {
  user: User | null;
  token: string | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthCtx>({
  user: null,
  token: null,
  setAuth: () => {},
  logout: () => {},
  isLoading: true,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('spectra_token');
    const storedUser = localStorage.getItem('spectra_user');
    if (stored && storedUser) {
      setToken(stored);
      try { setUser(JSON.parse(storedUser)); } catch {}
    }
    setIsLoading(false);
  }, []);

  const setAuth = useCallback((tok: string, u: User) => {
    localStorage.setItem('spectra_token', tok);
    localStorage.setItem('spectra_user', JSON.stringify(u));
    setToken(tok);
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('spectra_token');
    localStorage.removeItem('spectra_user');
    setToken(null);
    setUser(null);
    window.location.href = '/login';
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, setAuth, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
