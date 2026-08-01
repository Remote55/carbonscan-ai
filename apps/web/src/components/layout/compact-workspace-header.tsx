export interface CompactWorkspaceHeaderProps {
  title: string;
  mode: string;
  backHref: string;
}

export function CompactWorkspaceHeader({ title, mode, backHref }: CompactWorkspaceHeaderProps) {
  return (
    <header className="border-b border-hairline bg-paper">
      <div className="mx-auto flex min-h-16 max-w-7xl items-center gap-5 px-5 sm:px-8">
        <nav aria-label="Workspace navigation">
          {/* A bare text link next to a heading read as a stray word rather
              than a control. Same destination, shaped like something you press. */}
          <a
            href={backHref}
            className="focus-ring inline-flex items-center gap-1.5 rounded-full border border-hairline px-3.5 py-1.5 text-sm font-medium text-canopy transition-colors hover:border-moss hover:text-deep-forest"
          >
            <span aria-hidden>←</span>
            ย้อนกลับ
          </a>
        </nav>
        <div className="min-w-0">
          <h1 className="truncate font-display text-xl font-semibold text-forest-ink">{title}</h1>
          {/* Thai, so not font-mono - that face has no Thai glyphs and would
              drop this line to a silent fallback a size smaller. */}
          <p className="editorial-eyebrow-th text-canopy">{mode}</p>
        </div>
      </div>
    </header>
  );
}
