'use client';

interface JobDescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
}

const MIN_LENGTH = 50;
const PLACEHOLDER = `Paste the job description here...

Example:
We are looking for a Backend Software Engineer with 3+ years of Python experience.
Required skills: FastAPI, PostgreSQL, Docker, REST APIs.
Responsibilities: Design scalable microservices, write clean code, collaborate with product teams.`;

export function JobDescriptionInput({ value, onChange }: JobDescriptionInputProps) {
  const charCount = value.length;
  const isShort = charCount > 0 && charCount < MIN_LENGTH;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="section-label">Job Description</label>
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
    </div>
  );
}
