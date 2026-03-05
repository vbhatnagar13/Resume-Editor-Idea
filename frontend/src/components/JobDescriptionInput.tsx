'use client';

import { useRef, useState } from 'react';

interface JobDescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
  onJdFileSelect?: (file: File | null) => void;
  selectedJdFile?: File | null;
}

const MIN_LENGTH = 50;
const PLACEHOLDER = `Paste the job description here...

Example:
We are looking for a Backend Software Engineer with 3+ years of Python experience.
Required skills: FastAPI, PostgreSQL, Docker, REST APIs.
Responsibilities: Design scalable microservices, write clean code, collaborate with product teams.`;

export function JobDescriptionInput({
  value,
  onChange,
  onJdFileSelect,
  selectedJdFile,
}: JobDescriptionInputProps) {
  const [mode, setMode] = useState<'paste' | 'file'>('paste');
  const [fileError, setFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const charCount = value.length;
  const isShort = mode === 'paste' && charCount > 0 && charCount < MIN_LENGTH;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    if (!f) return;
    if (!f.name.endsWith('.txt')) {
      setFileError('Only .txt files are supported for JD upload.');
      return;
    }
    if (f.size > 1024 * 1024) {
      setFileError('File must be under 1 MB.');
      return;
    }
    setFileError(null);
    onJdFileSelect?.(f);
    // Also read file content into textarea for preview
    const reader = new FileReader();
    reader.onload = ev => onChange(ev.target?.result as string ?? '');
    reader.readAsText(f);
  };

  const clearFile = () => {
    onJdFileSelect?.(null);
    onChange('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="space-y-2">
      {/* Mode toggle */}
      <div className="flex items-center justify-between">
        <label className="section-label">Job Description</label>
        <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5 text-xs">
          <button
            type="button"
            onClick={() => { setMode('paste'); clearFile(); }}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              mode === 'paste' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Paste
          </button>
          <button
            type="button"
            onClick={() => setMode('file')}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              mode === 'file' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Upload .txt
          </button>
        </div>
      </div>

      {mode === 'file' ? (
        <div>
          {selectedJdFile ? (
            <div className="flex items-center gap-3 p-3 rounded-lg border border-green-300 bg-green-50">
              <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-green-700 font-medium flex-1 truncate">{selectedJdFile.name}</span>
              <button type="button" onClick={clearFile} className="text-xs text-green-600 underline flex-shrink-0">
                Remove
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full border-2 border-dashed border-gray-300 hover:border-brand-400 rounded-xl p-6 text-center transition-colors"
            >
              <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              <p className="text-sm text-gray-600">
                <span className="text-brand-600 underline font-medium">Choose a .txt file</span>
              </p>
              <p className="text-xs text-gray-400 mt-1">Max 1 MB</p>
            </button>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt"
            className="hidden"
            onChange={handleFileChange}
          />
          {fileError && (
            <p className="text-xs text-red-600 mt-1">{fileError}</p>
          )}
          {/* Preview textarea when file loaded */}
          {selectedJdFile && value && (
            <div className="mt-2">
              <p className="text-xs text-gray-500 mb-1">Preview:</p>
              <textarea
                value={value}
                readOnly
                rows={6}
                className="input-base resize-y font-mono text-xs leading-relaxed bg-gray-50 text-gray-600"
              />
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="flex justify-end">
            <span className={`text-xs ${isShort ? 'text-amber-500' : 'text-gray-400'}`}>
              {charCount} chars{isShort ? ` (min ${MIN_LENGTH})` : ''}
            </span>
          </div>
          <textarea
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={PLACEHOLDER}
            rows={10}
            className={`
              input-base resize-y font-mono text-xs leading-relaxed
              ${isShort ? 'border-amber-400 focus:ring-amber-400' : ''}
            `}
          />
          {isShort && (
            <p className="text-xs text-amber-600">
              Please paste the full job description for best results.
            </p>
          )}
        </>
      )}
    </div>
  );
}
