'use client';

import type { TailorSettings } from '@/lib/types';

interface TailoringSettingsProps {
  settings: TailorSettings;
  onChange: (settings: TailorSettings) => void;
}

const AGGRESSIVENESS_OPTIONS: {
  value: TailorSettings['aggressiveness'];
  label: string;
  description: string;
}[] = [
  {
    value: 'conservative',
    label: 'Conservative',
    description: 'Minimal edits, no reordering. Only rewrites bullets with low keyword overlap.',
  },
  {
    value: 'balanced',
    label: 'Balanced',
    description: 'Moderate rewrites with smart keyword insertion. May reorder entries for relevance.',
  },
  {
    value: 'aggressive',
    label: 'Aggressive',
    description: 'Full optimization: rewrites all bullets, reorders sections for maximum ATS impact.',
  },
];

export function TailoringSettings({ settings, onChange }: TailoringSettingsProps) {
  const update = (patch: Partial<TailorSettings>) =>
    onChange({ ...settings, ...patch });

  return (
    <div className="space-y-5">
      <div>
        <label className="section-label">Tailoring Mode</label>
        <div className="space-y-2">
          {AGGRESSIVENESS_OPTIONS.map(opt => (
            <label
              key={opt.value}
              className={`
                flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors duration-100
                ${settings.aggressiveness === opt.value
                  ? 'border-brand-500 bg-brand-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}
              `}
            >
              <input
                type="radio"
                name="aggressiveness"
                value={opt.value}
                checked={settings.aggressiveness === opt.value}
                onChange={() => update({ aggressiveness: opt.value })}
                className="mt-0.5 text-brand-600 focus:ring-brand-500"
              />
              <div>
                <span className="font-medium text-sm text-gray-900">{opt.label}</span>
                <p className="text-xs text-gray-500 mt-0.5">{opt.description}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <label className="section-label">Options</label>

        <label className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer">
          <div>
            <span className="text-sm font-medium text-gray-900">Keyword Emphasis</span>
            <p className="text-xs text-gray-500">Prioritize inserting exact JD keywords</p>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={settings.keyword_emphasis}
            onClick={() => update({ keyword_emphasis: !settings.keyword_emphasis })}
            className={`
              relative w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0
              ${settings.keyword_emphasis ? 'bg-brand-600' : 'bg-gray-300'}
            `}
          >
            <span
              className={`
                absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200
                ${settings.keyword_emphasis ? 'translate-x-5' : 'translate-x-0'}
              `}
            />
          </button>
        </label>

        <label className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer">
          <div>
            <span className="text-sm font-medium text-gray-900">Lock Section Order</span>
            <p className="text-xs text-gray-500">Never reorder sections or entries</p>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={settings.no_reordering}
            onClick={() => update({ no_reordering: !settings.no_reordering })}
            className={`
              relative w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0
              ${settings.no_reordering ? 'bg-brand-600' : 'bg-gray-300'}
            `}
          >
            <span
              className={`
                absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200
                ${settings.no_reordering ? 'translate-x-5' : 'translate-x-0'}
              `}
            />
          </button>
        </label>
      </div>
    </div>
  );
}
