'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('spectra_token');
}

export interface ScanProgressEvent {
  scan_id: string;
  org_id: string;
  stage: string;
  status: string;
  message: string;
  progress_pct: number;
  timestamp: string;
  findings_count?: number;
  critical_count?: number;
  high_count?: number;
  type?: string;
}

export function useScanSSE(scanId: string | null) {
  const [event, setEvent] = useState<ScanProgressEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!scanId) return;
    const token = getToken();
    if (!token) return;

    const url = `${API_URL}/api/v1/events/scans/${scanId}/stream?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => setConnected(true);

    es.onmessage = (e) => {
      try {
        const data: ScanProgressEvent = JSON.parse(e.data);
        if (data.type === 'close') {
          es.close();
          setConnected(false);
          return;
        }
        setEvent(data);
      } catch {}
    };

    es.onerror = () => {
      setConnected(false);
      es.close();
    };

    return () => {
      es.close();
      setConnected(false);
    };
  }, [scanId]);

  return { event, connected };
}

export function useDashboardSSE() {
  const [event, setEvent] = useState<ScanProgressEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;

    const url = `${API_URL}/api/v1/events/stream?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => setConnected(true);

    es.onmessage = (e) => {
      try {
        const data: ScanProgressEvent = JSON.parse(e.data);
        if (data.type !== 'close') {
          setEvent(data);
        }
      } catch {}
    };

    es.onerror = () => {
      setConnected(false);
      // Reconnect after 5s
      setTimeout(() => {
        if (esRef.current === es) {
          es.close();
        }
      }, 5000);
    };

    return () => {
      es.close();
      setConnected(false);
    };
  }, []);

  return { event, connected };
}
