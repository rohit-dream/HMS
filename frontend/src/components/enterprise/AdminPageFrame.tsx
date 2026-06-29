import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { breadcrumbsFromPath } from "@/lib/breadcrumbs";
import { cn } from "@/lib/cn";

export interface AdminPageFrameProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  pathname?: string;
}

export function AdminPageFrame({
  title,
  description,
  actions,
  children,
  className,
  pathname,
}: AdminPageFrameProps) {
  const location = useLocation();
  const crumbs = breadcrumbsFromPath(pathname ?? location.pathname);

  return (
    <div className={cn("mx-auto w-full max-w-7xl space-y-6 animate-fade-in", className)}>
      <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1 text-xs text-muted">
        {crumbs.map((crumb, index) => (
          <span key={`${crumb.label}-${index}`} className="inline-flex items-center gap-1">
            {index > 0 && <ChevronRight className="h-3 w-3 opacity-50" aria-hidden />}
            {crumb.href ? (
              <Link to={crumb.href} className="transition-colors hover:text-foreground">
                {crumb.label}
              </Link>
            ) : (
              <span className="text-foreground/80">{crumb.label}</span>
            )}
          </span>
        ))}
      </nav>

      <header className="flex flex-col gap-4 border-b border-border-light pb-6 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-3xl">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">{title}</h1>
          {description && <p className="mt-2 text-sm leading-relaxed text-muted">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
      </header>

      <div className="space-y-6">{children}</div>
    </div>
  );
}
