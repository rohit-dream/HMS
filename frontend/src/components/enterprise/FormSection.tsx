import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface FormSectionProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
  columns?: 1 | 2 | 3;
}

const columnClasses = {
  1: "grid-cols-1",
  2: "grid-cols-1 md:grid-cols-2",
  3: "grid-cols-1 md:grid-cols-2 xl:grid-cols-3",
};

export function FormSection({
  title,
  description,
  children,
  className,
  columns = 2,
}: FormSectionProps) {
  return (
    <section className={cn("space-y-4", className)}>
      <div className="border-b border-border-light pb-4">
        <h3 className="text-base font-semibold text-foreground">{title}</h3>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      <div className={cn("grid gap-4", columnClasses[columns])}>{children}</div>
    </section>
  );
}

export function FormPageLayout({
  children,
  sidebar,
  className,
}: {
  children: ReactNode;
  sidebar?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]", className)}>
      <div className="glass-panel-strong space-y-8 p-6 sm:p-8">{children}</div>
      {sidebar && (
        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">{sidebar}</aside>
      )}
    </div>
  );
}

export function FormHelpCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="glass-panel p-5 text-sm">
      <h4 className="font-semibold text-foreground">{title}</h4>
      <div className="mt-2 space-y-2 text-muted">{children}</div>
    </div>
  );
}
