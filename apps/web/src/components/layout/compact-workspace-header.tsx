export interface CompactWorkspaceHeaderProps {
  title: string;
  mode: string;
  backHref: string;
}

export function CompactWorkspaceHeader({ title, mode, backHref }: CompactWorkspaceHeaderProps) {
  return (
    <header className="border-b border-hairline bg-paper">
      <div className="mx-auto flex min-h-16 max-w-7xl items-center gap-4 px-5 sm:px-8">
        <nav aria-label="Workspace navigation">
          <a href={backHref} className="focus-ring rounded-md text-sm font-medium text-canopy hover:text-deep-forest">
            Back
          </a>
        </nav>
        <div className="min-w-0 border-l border-hairline pl-4">
          <h1 className="truncate font-display text-xl font-semibold text-forest-ink">{title}</h1>
          <p className="font-mono text-[0.6875rem] uppercase tracking-[0.14em] text-canopy">{mode}</p>
        </div>
      </div>
    </header>
  );
}
