export interface StatusStateProps {
  label: string;
  value: string;
  note?: string;
  tone: 'ready' | 'warning' | 'unavailable';
}

const toneClasses = {
  ready: 'border-moss/40 bg-lichen/35 text-deep-forest',
  warning: 'border-evidence-amber/45 bg-evidence-amber/15 text-forest-ink',
  unavailable: 'border-clay/40 bg-clay/10 text-forest-ink',
};

export function StatusState({ label, value, note, tone }: StatusStateProps) {
  return (
    <article data-tone={tone} className={`rounded-[1.25rem] border p-5 ${toneClasses[tone]}`}>
      <p className="editorial-eyebrow">{label}</p>
      <p className="mt-3 font-display text-2xl font-semibold">{value}</p>
      {note ? <p className="mt-2 font-mono text-[0.6875rem] leading-5">{note}</p> : null}
    </article>
  );
}
