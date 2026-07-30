export interface EvidenceMetricProps {
  label: string;
  value: string;
  note?: string;
  tone?: 'paper' | 'dark' | 'lichen';
}

const toneClasses = {
  paper: 'bg-paper text-forest-ink',
  dark: 'border-deep-forest bg-deep-forest text-paper [&_.editorial-eyebrow]:text-lichen',
  lichen: 'border-lichen bg-lichen/45 text-deep-forest',
};

export function EvidenceMetric({ label, value, note, tone = 'paper' }: EvidenceMetricProps) {
  return (
    <article data-tone={tone} className={`rounded-[1.25rem] border border-hairline p-5 ${toneClasses[tone]}`}>
      <p className="editorial-eyebrow">{label}</p>
      <p className="mt-3 font-display text-3xl tabular-nums">{value}</p>
      {note ? <p className="mt-2 font-mono text-[0.6875rem]">{note}</p> : null}
    </article>
  );
}
