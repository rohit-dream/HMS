import type { ReactNode } from "react";

interface AuthLayoutProps {
  children?: ReactNode;
  wide?: boolean;
}

export function AuthLayout({ children, wide = false }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface p-4">
      <div
        className={`w-full rounded-xl border border-border bg-white p-8 shadow-sm ${wide ? "max-w-lg" : "max-w-md"}`}
      >
        {children ?? (
          <p className="text-center text-sm text-muted">Authentication screens — Sprint 2</p>
        )}
      </div>
    </div>
  );
}
