import { forwardRef, type InputHTMLAttributes, type SelectHTMLAttributes } from "react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

const fieldClassName =
  "w-full rounded-lg border border-border px-3 py-2 outline-none ring-primary focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60";

export const inputClassName = fieldClassName;

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, error, ...props },
  ref,
) {
  return (
    <div className="space-y-1">
      <input
        ref={ref}
        className={cn(fieldClassName, error && "border-error ring-error", className)}
        aria-invalid={error ? true : undefined}
        {...props}
      />
      {error && <p className="text-xs text-error">{error}</p>}
    </div>
  );
});

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { className, error, children, ...props },
  ref,
) {
  return (
    <div className="space-y-1">
      <select
        ref={ref}
        className={cn(fieldClassName, error && "border-error ring-error", className)}
        aria-invalid={error ? true : undefined}
        {...props}
      >
        {children}
      </select>
      {error && <p className="text-xs text-error">{error}</p>}
    </div>
  );
});

export const labelClassName = "block space-y-1 text-sm";
export const labelTextClassName = "font-medium text-slate-700";

export interface FieldLabelProps {
  htmlFor?: string;
  label?: string;
  children?: ReactNode;
  className?: string;
}

export function FieldLabel({ htmlFor, label, children, className }: FieldLabelProps) {
  if (label !== undefined) {
    return (
      <div className={cn(labelClassName, className)}>
        <label htmlFor={htmlFor} className={labelTextClassName}>
          {label}
        </label>
        {children}
      </div>
    );
  }

  return (
    <label htmlFor={htmlFor} className={cn(labelClassName, className)}>
      {children}
    </label>
  );
}
