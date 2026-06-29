import type { ReactNode } from "react";
import {
  Controller,
  type Control,
  type FieldPath,
  type FieldValues,
} from "react-hook-form";
import { FieldLabel, Input, Select } from "@/components/ui/Input";
import { cn } from "@/lib/cn";

type FieldElement = "input" | "select" | "textarea";

interface FormFieldBaseProps<T extends FieldValues> {
  name: FieldPath<T>;
  control: Control<T>;
  label: string;
  className?: string;
  description?: string;
}

interface InputFieldProps<T extends FieldValues> extends FormFieldBaseProps<T> {
  as?: "input";
  type?: React.HTMLInputTypeAttribute;
  placeholder?: string;
}

interface SelectFieldProps<T extends FieldValues> extends FormFieldBaseProps<T> {
  as: "select";
  children: ReactNode;
}

interface TextareaFieldProps<T extends FieldValues> extends FormFieldBaseProps<T> {
  as: "textarea";
  rows?: number;
  placeholder?: string;
}

export type FormFieldProps<T extends FieldValues> =
  | InputFieldProps<T>
  | SelectFieldProps<T>
  | TextareaFieldProps<T>;

export function FormField<T extends FieldValues>(props: FormFieldProps<T>) {
  const { name, control, label, className, description } = props;
  const fieldAs: FieldElement = props.as ?? "input";

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState }) => {
        const error = fieldState.error?.message;
        const fieldId = String(name);

        return (
          <div className={cn("space-y-1.5", className)}>
            <FieldLabel htmlFor={fieldId} label={label} />
            {description && <p className="text-xs text-muted">{description}</p>}
            {fieldAs === "select" ? (
              <Select
                id={fieldId}
                error={error}
                {...field}
                value={field.value ?? ""}
                onChange={(event) => field.onChange(event.target.value)}
              >
                {"children" in props ? props.children : null}
              </Select>
            ) : fieldAs === "textarea" ? (
              <textarea
                id={fieldId}
                rows={"rows" in props ? props.rows ?? 3 : 3}
                placeholder={"placeholder" in props ? props.placeholder : undefined}
                className={cn(
                  "glass-textarea",
                  error && "border-error/50 ring-2 ring-error/30",
                )}
                aria-invalid={error ? true : undefined}
                {...field}
                value={field.value ?? ""}
              />
            ) : (
              <Input
                id={fieldId}
                type={"type" in props ? props.type : undefined}
                placeholder={"placeholder" in props ? props.placeholder : undefined}
                error={error}
                {...field}
                value={field.value ?? ""}
              />
            )}
            {fieldAs === "textarea" && error && <p className="text-xs text-error">{error}</p>}
          </div>
        );
      }}
    />
  );
}
