import { Link } from "react-router-dom";
import { Clock } from "lucide-react";
import { AdminPageFrame } from "@/components/enterprise";
import { GlassCard } from "@/components/ui/GlassCard";

interface ModulePlaceholderPageProps {
  title: string;
  description?: string;
}

export function ModulePlaceholderPage({ title, description }: ModulePlaceholderPageProps) {
  return (
    <AdminPageFrame
      title={title}
      description={description ?? "Scheduled for a future sprint release."}
    >
      <GlassCard strong padding="lg" className="text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-surface-secondary">
          <Clock className="h-7 w-7 text-muted" aria-hidden />
        </div>
        <h3 className="mt-4 text-lg font-semibold text-foreground">Module in development</h3>
        <p className="mx-auto mt-2 max-w-lg text-sm text-muted">
          This clinical workflow is part of the HMS roadmap. Your organization can continue configuring
          hospital structure and administration while this module is being delivered.
        </p>
        <Link
          to="/dashboard"
          className="mt-6 inline-flex rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-white shadow-card"
        >
          Return to command center
        </Link>
      </GlassCard>
    </AdminPageFrame>
  );
}
