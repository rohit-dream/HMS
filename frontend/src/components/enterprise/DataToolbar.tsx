import type { FormEvent, ReactNode } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/cn";

export interface DataToolbarProps {
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  onSearchSubmit?: (event: FormEvent) => void;
  searchPlaceholder?: string;
  filters?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function DataToolbar({
  searchValue,
  onSearchChange,
  onSearchSubmit,
  searchPlaceholder = "Search…",
  filters,
  actions,
  className,
}: DataToolbarProps) {
  return (
    <div
      className={cn(
        "glass-panel flex flex-col gap-3 p-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between",
        className,
      )}
    >
      <div className="flex min-w-0 flex-1 flex-col gap-3 sm:flex-row sm:items-center">
        {onSearchSubmit && onSearchChange !== undefined && searchValue !== undefined && (
          <form className="relative min-w-[14rem] flex-1 sm:max-w-md" onSubmit={onSearchSubmit}>
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
              aria-hidden
            />
            <Input
              className="pl-9"
              placeholder={searchPlaceholder}
              value={searchValue}
              onChange={(event) => onSearchChange(event.target.value)}
            />
          </form>
        )}
        {filters && <div className="flex flex-wrap items-center gap-2">{filters}</div>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
