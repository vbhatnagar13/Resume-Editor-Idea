'use client';

interface KeywordScoreCardProps {
  scoreBefore: number;  // 0–1
  scoreAfter: number;   // 0–1
  keywordsAdded: string[];
  keywordsPreserved: string[];
}

function ScoreRing({ score, label }: { score: number; label: string }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 70 ? 'text-green-600' : pct >= 40 ? 'text-amber-500' : 'text-red-500';
  const bg =
    pct >= 70 ? 'bg-green-50 border-green-200' : pct >= 40 ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200';

  return (
    <div className={`flex flex-col items-center justify-center rounded-xl border p-4 gap-1 ${bg}`}>
      <span className={`text-3xl font-bold ${color}`}>{pct}%</span>
      <span className="text-xs text-gray-500 font-medium">{label}</span>
    </div>
  );
}

export function KeywordScoreCard({
  scoreBefore,
  scoreAfter,
  keywordsAdded,
  keywordsPreserved,
}: KeywordScoreCardProps) {
  const improvement = Math.round((scoreAfter - scoreBefore) * 100);
  const hasImprovement = improvement > 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Keyword Coverage</h3>
        {hasImprovement && (
          <span className="text-xs font-semibold text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
            +{improvement}pp improvement
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <ScoreRing score={scoreBefore} label="Before" />
        <ScoreRing score={scoreAfter} label="After" />
      </div>

      {keywordsAdded.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-600 mb-1.5">Keywords Added</p>
          <div className="flex flex-wrap gap-1.5">
            {keywordsAdded.map((kw, i) => (
              <span
                key={`added-${kw}-${i}`}
                className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full"
              >
                + {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {keywordsPreserved.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-600 mb-1.5">Already Covered</p>
          <div className="flex flex-wrap gap-1.5">
            {keywordsPreserved.slice(0, 15).map((kw, i) => (
              <span
                key={`preserved-${kw}-${i}`}
                className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded-full"
              >
                ✓ {kw}
              </span>
            ))}
            {keywordsPreserved.length > 15 && (
              <span className="text-xs text-gray-400 self-center">
                +{keywordsPreserved.length - 15} more
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
