'use client';

import type { DiffChange, DiffReport } from '@/lib/types';
import { useState } from 'react';

interface DiffViewerProps {
  diffReport: DiffReport;
}

const CHANGE_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  rewrite: { label: 'Rewrite', color: 'bg-blue-100 text-blue-700' },
  keyword_add: { label: 'Keyword Added', color: 'bg-green-100 text-green-700' },
  reorder: { label: 'Reordered', color: 'bg-amber-100 text-amber-700' },
};

function ChangeCard({ change, index }: { change: DiffChange; index: number }) {
  const [expanded, setExpanded] = useState(index < 3);
  const meta = CHANGE_TYPE_LABELS[change.change_type] ?? {
    label: change.change_type,
    color: 'bg-gray-100 text-gray-600',
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${meta.color}`}>
            {meta.label}
          </span>
          <span className="text-xs text-gray-500 flex-shrink-0">{change.section}</span>
          <span className="text-sm text-gray-700 truncate">{change.original}</span>
        </div>
        <svg
          className={`w-4 h-4 text-gray-400 flex-shrink-0 ml-2 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="p-4 space-y-3 bg-white">
          {change.change_type !== 'reorder' ? (
            <>
              <div>
                <p className="text-xs font-semibold text-red-600 mb-1">Original</p>
                <p className="text-sm bg-red-50 border border-red-200 rounded p-2 text-gray-800 leading-relaxed">
                  {change.original}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold text-green-600 mb-1">Revised</p>
                <p className="text-sm bg-green-50 border border-green-200 rounded p-2 text-gray-800 leading-relaxed">
                  {change.revised}
                </p>
              </div>
            </>
          ) : (
            <div>
              <p className="text-xs font-semibold text-amber-600 mb-1">Reordering</p>
              <p className="text-sm text-gray-600">{change.reason}</p>
            </div>
          )}
          {change.reason && change.change_type !== 'reorder' && (
            <p className="text-xs text-gray-500 italic">{change.reason}</p>
          )}
        </div>
      )}
    </div>
  );
}

export function DiffViewer({ diffReport }: DiffViewerProps) {
  const { changes, keywords_added, keywords_preserved, fabrication_check, ats_check } =
    diffReport;

  const fabricationOk = fabrication_check === 'passed';
  const atsOk = ats_check === 'ATS-friendly';

  return (
    <div className="space-y-6">
      {/* Status badges */}
      <div className="flex flex-wrap gap-3">
        <div
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium ${
            fabricationOk
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            {fabricationOk ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            )}
          </svg>
          {fabricationOk ? 'No fabrication detected' : fabrication_check}
        </div>

        <div
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium ${
            atsOk
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-amber-50 text-amber-700 border border-amber-200'
          }`}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          {ats_check}
        </div>

        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
          {changes.length} change{changes.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Keywords */}
      {keywords_added.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-gray-700 mb-2">Keywords Added</p>
          <div className="flex flex-wrap gap-2">
            {keywords_added.map((kw, i) => (
              <span
                key={`${kw}-${i}`}
                className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full"
              >
                + {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Changes list */}
      {changes.length > 0 ? (
        <div>
          <p className="text-sm font-semibold text-gray-700 mb-3">Changes</p>
          <div className="space-y-2">
            {changes.map((change, i) => (
              <ChangeCard key={change.bullet_id ?? change.entry_id ?? i} change={change} index={i} />
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="font-medium">No changes needed</p>
          <p className="text-sm mt-1">Your resume already aligns well with the job description.</p>
        </div>
      )}
    </div>
  );
}
