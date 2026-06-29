import type { ReactNode } from "react";
import type { PaginationMeta } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";

export interface PaginationBarProps {
  pagination: PaginationMeta;
  onPageChange: (page: number) => void;
  className?: string;
}

export function PaginationBar({ pagination, onPageChange, className }: PaginationBarProps) {
  const { page, total_pages, total_items, page_size } = pagination;
  const start = total_items === 0 ? 0 : (page - 1) * page_size + 1;
  const end = Math.min(page * page_size, total_items);

  return (
    <div
      className={cn(
        "flex flex-col gap-3 border-t border-border-light px-4 py-3 text-sm text-muted sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      <p>
        Showing <span className="text-foreground">{start}</span>–<span className="text-foreground">{end}</span> of{" "}
        <span className="text-foreground">{total_items}</span>
      </p>
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <span className="min-w-[5rem] text-center text-foreground">
          Page {page} / {Math.max(total_pages, 1)}
        </span>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          disabled={page >= total_pages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

export function DataGridShell({
  children,
  footer,
  className,
}: {
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("overflow-hidden rounded-xl border border-border-light bg-card shadow-card", className)}>
      <div className="max-h-[calc(100vh-20rem)] overflow-auto">{children}</div>
      {footer}
    </div>
  );
}
