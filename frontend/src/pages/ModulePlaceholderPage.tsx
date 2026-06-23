interface ModulePlaceholderPageProps {
  title: string;
  description?: string;
}

export function ModulePlaceholderPage({ title, description }: ModulePlaceholderPageProps) {
  return (
    <div className="space-y-3 rounded-lg border border-border bg-white p-8">
      <h2 className="text-2xl font-semibold text-slate-900">{title}</h2>
      <p className="text-muted">
        {description ?? "This module will be available in an upcoming sprint."}
      </p>
    </div>
  );
}
