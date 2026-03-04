'use client';

import DOMPurify from 'dompurify';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { DiffViewer } from '@/components/DiffViewer';
import { DownloadButtons } from '@/components/DownloadButtons';
import type { TailorResponse } from '@/lib/types';

function ReviewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session');

  const [result, setResult] = useState<TailorResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'diff' | 'preview'>('diff');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) {
      setError('No session found. Please go back and upload your resume.');
      return;
    }
    const stored = sessionStorage.getItem(`tailor_result_${sessionId}`);
    if (!stored) {
      setError('Session data not found. Please go back and try again.');
      return;
    }
    try {
      setResult(JSON.parse(stored));
    } catch {
      setError('Failed to load results. Please try again.');
    }
  }, [sessionId]);

  if (error) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <div className="text-5xl mb-4">⚠️</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h1>
        <p className="text-gray-600 mb-6">{error}</p>
        <button
          type="button"
          onClick={() => router.push('/')}
          className="btn-primary"
        >
          Start Over
        </button>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center py-24">
        <svg className="w-8 h-8 text-brand-600 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  const { diff_report, preview_html } = result;
  const totalChanges = diff_report.changes.length;

  const safePreviewHtml = useMemo(() => {
    if (typeof window === 'undefined') return '';
    // Defense in depth: the backend already escapes HTML entities via _escape() in
    // generator._build_preview_html, so preview_html should contain no raw tags from
    // resume content. DOMPurify provides a second layer against any unexpected markup.
    return DOMPurify.sanitize(preview_html, {
      ALLOWED_TAGS: ['div', 'h1', 'h2', 'h3', 'p', 'ul', 'li', 'hr', 'strong', 'em', 'span', 'br'],
      ALLOWED_ATTR: ['class'],
    });
  }, [preview_html]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Review Your Tailored Resume</h1>
          <p className="text-gray-600 mt-1">
            {totalChanges > 0
              ? `${totalChanges} change${totalChanges !== 1 ? 's' : ''} made to improve keyword alignment`
              : 'Your resume is already well-aligned with the job description'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => router.push('/')}
          className="btn-secondary"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Start Over
        </button>
      </div>

      {/* Download */}
      <div className="card">
        <DownloadButtons sessionId={result.session_id} />
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-6">
          {(['diff', 'preview'] as const).map(tab => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`
                pb-3 text-sm font-medium border-b-2 transition-colors duration-150 capitalize
                ${activeTab === tab
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'}
              `}
            >
              {tab === 'diff' ? `Changes (${totalChanges})` : 'Preview'}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === 'diff' ? (
        <div className="card">
          <DiffViewer diffReport={diff_report} />
        </div>
      ) : (
        <div className="card prose max-w-none">
          <style>{`
            .resume-preview h1 { font-size: 1.5rem; font-weight: bold; text-align: center; margin-bottom: 0.25rem; }
            .resume-preview h2 { font-size: 1rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 1rem; margin-bottom: 0.25rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.25rem; }
            .resume-preview ul { list-style: disc; padding-left: 1.5rem; margin: 0.5rem 0; }
            .resume-preview li { margin-bottom: 0.25rem; font-size: 0.9rem; }
            .resume-preview p { margin: 0.25rem 0; font-size: 0.9rem; }
            .resume-preview hr { border: none; border-top: 1px solid #e5e7eb; }
          `}</style>
          <div
            dangerouslySetInnerHTML={{ __html: safePreviewHtml }}
          />
        </div>
      )}

      {/* Keywords summary */}
      {diff_report.keywords_added.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Keywords Added ({diff_report.keywords_added.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {diff_report.keywords_added.map(kw => (
              <span
                key={kw}
                className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full"
              >
                + {kw}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReviewPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-24">
          <svg className="w-8 h-8 text-brand-600 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      }
    >
      <ReviewContent />
    </Suspense>
  );
}
