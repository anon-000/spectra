'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  page: number;
  pageSize: number;
  count: number; // items on current page
  onPage: (p: number) => void;
}

export function Pagination({ page, pageSize, count, onPage }: PaginationProps) {
  const isFirst = page === 1;
  const isLast = count < pageSize;

  return (
    <div className="flex items-center gap-3 text-sm text-slate-400">
      <button
        onClick={() => onPage(page - 1)}
        disabled={isFirst}
        className="p-1.5 rounded-md hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition"
      >
        <ChevronLeft size={16} />
      </button>
      <span>Page <span className="text-white font-medium">{page}</span></span>
      <button
        onClick={() => onPage(page + 1)}
        disabled={isLast}
        className="p-1.5 rounded-md hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
