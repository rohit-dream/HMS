import { APP_NAME } from "@/lib/constants";

export function Header() {
  return (
    <header className="flex items-center justify-between border-b border-border bg-white px-6 py-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">{APP_NAME}</h1>
        <p className="text-sm text-muted">Foundation shell — auth coming Sprint 2</p>
      </div>
      <div className="rounded-full bg-surface px-3 py-1 text-sm text-muted">Guest</div>
    </header>
  );
}
