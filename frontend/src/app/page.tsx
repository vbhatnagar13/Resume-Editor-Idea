'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { FileUpload } from '@/components/FileUpload';
import { JobDescriptionInput } from '@/components/JobDescriptionInput';
import { TailoringSettings } from '@/components/TailoringSettings';
import { tailorResume, uploadResume } from '@/lib/api';
import type { TailorSettings } from '@/lib/types';

const DEFAULT_SETTINGS: TailorSettings = {
  aggressiveness: 'balanced',
  keyword_emphasis: true,
  no_reordering: false,
};

type Step = 'idle' | 'uploading' | 'tailoring' | 'done' | 'error';

const STEP_LABELS: Record<Step, string> = {
  idle: '',
  uploading: 'Uploading resume…',
  tailoring: 'Tailoring your resume with AI… (this may take 30–60 seconds)',
  done: 'Done!',
  error: 'Error',
};

export default function HomePage() {
  const router = useRouter();

  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [settings, setSettings] = useState<TailorSettings>(DEFAULT_SETTINGS);
  const [step, setStep] = useState<Step>('idle');
  const [error, setError] = useState<string | null>(null);

  const canSubmit =
    file !== null &&
    jobDescription.trim().length >= 50 &&
    step === 'idle';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit || !file) return;

    setError(null);

    try {
      setStep('uploading');
      const { session_id } = await uploadResume(file, jobDescription);

      setStep('tailoring');
      const response = await tailorResume({
        session_id,
        job_description: jobDescription,
        ...settings,
      });

      // Store response in sessionStorage for the review page
      sessionStorage.setItem(
        `tailor_result_${session_id}`,
        JSON.stringify(response),
      );

      setStep('done');
      router.push(`/review?session=${session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setStep('error');
    }
  };

  const isLoading = step === 'uploading' || step === 'tailoring';

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-bold text-gray-900">
          Tailor Your Resume with AI
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Upload your resume and paste a job description. Our AI will rewrite your
          bullet points to match the role — without fabricating any experience.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <FileUpload onFileSelect={setFile} selectedFile={file} />
        </div>

        <div className="card">
          <JobDescriptionInput
            value={jobDescription}
            onChange={setJobDescription}
          />
        </div>

        <div className="card">
          <h2 className="text-base font-semibold text-gray-900 mb-4">
            Tailoring Options
          </h2>
          <TailoringSettings settings={settings} onChange={setSettings} />
        </div>

        {/* Error */}
        {step === 'error' && error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 flex gap-3">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="font-semibold text-red-800">Tailoring failed</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <button
                type="button"
                onClick={() => { setStep('idle'); setError(null); }}
                className="text-sm text-red-600 underline mt-2"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="rounded-lg bg-brand-50 border border-brand-200 p-4 flex items-center gap-3">
            <svg className="w-5 h-5 text-brand-600 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm text-brand-700 font-medium">{STEP_LABELS[step]}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={!canSubmit || isLoading}
          className="btn-primary w-full justify-center py-4 text-base"
        >
          {isLoading ? (
            <>
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Processing…
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Tailor My Resume
            </>
          )}
        </button>
      </form>

      <div className="grid grid-cols-3 gap-4 text-center">
        {[
          { icon: '🔒', title: 'Private', desc: 'Files are never stored permanently' },
          { icon: '✅', title: 'No Fabrication', desc: 'AI never invents experience' },
          { icon: '🎯', title: 'ATS-Ready', desc: 'Optimized for applicant tracking systems' },
        ].map(item => (
          <div key={item.title} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl mb-2">{item.icon}</div>
            <p className="font-semibold text-sm text-gray-900">{item.title}</p>
            <p className="text-xs text-gray-500 mt-1">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
