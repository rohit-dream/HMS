import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type BadgeVariant = "success" | "error" | "warning" | "info" | "neutral";

const variantClasses: Record<BadgeVariant, string> = {
  success: "border-emerald-200 bg-emerald-50 text-success",
  error: "border-red-200 bg-red-50 text-error",
  warning: "border-amber-200 bg-amber-50 text-warning",
  info: "border-blue-200 bg-blue-50 text-primary",
  neutral: "border-border-light bg-surface-secondary text-muted",
};

export function Badge({
  children,
  variant = "neutral",
  className,
}: {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium",
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
