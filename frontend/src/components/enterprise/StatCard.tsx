import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface StatCardProps {
  label: string;
  value: ReactNode;
  hint?: string;
  icon: LucideIcon;
  tone?: "primary" | "secondary" | "accent" | "success" | "warning";
  loading?: boolean;
  className?: string;
}

const toneClasses = {
  primary: "bg-blue-50 text-primary",
  secondary: "bg-gray-100 text-secondary",
  accent: "bg-teal-50 text-accent",
  success: "bg-emerald-50 text-success",
  warning: "bg-amber-50 text-warning",
};

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "primary",
  loading = false,
  className,
}: StatCardProps) {
  return (
    <article
      className={cn(
        "glass-panel glass-panel-hover flex flex-col gap-4 p-5",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className={cn("flex h-11 w-11 items-center justify-center rounded-2xl", toneClasses[tone])}>
          <Icon className="h-5 w-5" aria-hidden />
        </div>
        {hint && <span className="text-xs text-muted">{hint}</span>}
      </div>
      <div>
        <p className="text-sm text-muted">{label}</p>
        {loading ? (
          <div className="mt-2 h-8 w-20 animate-pulse rounded-lg bg-surface-secondary" />
        ) : (
          <p className="mt-1 text-3xl font-semibold tracking-tight text-foreground">{value}</p>
        )}
      </div>
    </article>
  );
}
