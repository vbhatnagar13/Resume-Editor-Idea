'use client';

import { useState } from 'react';
import { downloadFile, triggerDownload } from '@/lib/api';
import type { DownloadFormat } from '@/lib/types';

interface DownloadButtonsProps {
  sessionId: string;
}

export function DownloadButtons({ sessionId }: DownloadButtonsProps) {
  const [loading, setLoading] = useState<DownloadFormat | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async (format: DownloadFormat) => {
    setLoading(format);
    setError(null);
    try {
      const blob = await downloadFile(sessionId, format);
      triggerDownload(blob, `resume_tailored.${format}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-3">
      <p className="text-sm font-semibold text-gray-700">Download Tailored Resume</p>

      <div className="flex flex-col sm:flex-row gap-3">
        <button
          type="button"
          onClick={() => handleDownload('docx')}
          disabled={loading !== null}
          className="btn-primary flex-1 justify-center"
        >
          {loading === 'docx' ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          )}
          Download DOCX
        </button>

        <button
          type="button"
          onClick={() => handleDownload('pdf')}
          disabled={loading !== null}
          className="btn-secondary flex-1 justify-center"
        >
          {loading === 'pdf' ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          )}
          Download PDF
        </button>
      </div>

      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
