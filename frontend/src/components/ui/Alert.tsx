import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type AlertVariant = "success" | "error" | "warning" | "info";

const variantClasses: Record<AlertVariant, string> = {
  success: "border-emerald-200 bg-emerald-50 text-success",
  error: "border-red-200 bg-red-50 text-error",
  warning: "border-amber-200 bg-amber-50 text-warning",
  info: "border-blue-200 bg-blue-50 text-primary",
};

export function Alert({
  children,
  variant = "info",
  className,
}: {
  children: ReactNode;
  variant?: AlertVariant;
  className?: string;
}) {
  return (
    <p
      className={cn("rounded-lg border px-3 py-2.5 text-sm", variantClasses[variant], className)}
      role="status"
    >
      {children}
    </p>
  );
}
