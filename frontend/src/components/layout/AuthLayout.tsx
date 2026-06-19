import type { ReactNode } from "react";

interface AuthLayoutProps {
  children?: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface p-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-white p-8 shadow-sm">
        {children ?? (
          <p className="text-center text-sm text-muted">Authentication screens — Sprint 2</p>
        )}
      </div>
    </div>
  );
}
