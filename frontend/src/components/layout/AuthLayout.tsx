import type { ReactNode } from "react";
import { Activity, HeartPulse, ShieldCheck, Stethoscope } from "lucide-react";

interface AuthLayoutProps {
  children?: ReactNode;
  wide?: boolean;
}

const highlights = [
  { icon: HeartPulse, title: "Patient-first operations", text: "Built for hospitals, clinics, and care teams." },
  { icon: ShieldCheck, title: "Enterprise security", text: "Tenant isolation, RBAC, and audit-ready access." },
  { icon: Stethoscope, title: "Clinical workflows", text: "OPD, IPD, billing, and diagnostics in one platform." },
];

export function AuthLayout({ children, wide = false }: AuthLayoutProps) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden bg-sidebar lg:flex lg:flex-col">
        <div className="relative flex flex-1 flex-col justify-between p-10 xl:p-14">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
              <Activity className="h-6 w-6 text-white" aria-hidden />
            </div>
            <div>
              <p className="text-lg font-semibold text-white">HMS Platform</p>
              <p className="text-sm text-sidebar-text">Enterprise Hospital Management</p>
            </div>
          </div>

          <div className="max-w-lg space-y-8">
            <div>
              <h1 className="text-4xl font-semibold leading-tight tracking-tight text-white xl:text-5xl">
                Healthcare operations, designed for commercial deployment
              </h1>
              <p className="mt-4 text-base leading-relaxed text-sidebar-text">
                A professional foundation for hospitals that need secure administration, organization
                structure, and scalable clinical modules.
              </p>
            </div>

            <ul className="space-y-4">
              {highlights.map((item) => {
                const Icon = item.icon;
                return (
                  <li
                    key={item.title}
                    className="flex gap-4 rounded-xl border border-gray-600 bg-sidebar-active p-4"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gray-600">
                      <Icon className="h-5 w-5 text-gray-200" aria-hidden />
                    </div>
                    <div>
                      <p className="font-medium text-white">{item.title}</p>
                      <p className="mt-1 text-sm text-sidebar-text">{item.text}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>

          <p className="text-xs text-gray-500">Trusted architecture for multi-tenant hospital networks</p>
        </div>
      </div>

      <div className="flex items-center justify-center bg-surface px-4 py-10 sm:px-8">
        <div className={`auth-shell w-full ${wide ? "max-w-xl" : "max-w-md"}`}>
          <div className="mb-6 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Activity className="h-5 w-5 text-white" aria-hidden />
            </div>
            <div>
              <p className="font-semibold text-foreground">HMS Platform</p>
              <p className="text-xs text-muted">Enterprise Healthcare</p>
            </div>
          </div>

          <div className="rounded-xl border border-border-light bg-card p-8 shadow-card sm:p-10">
            {children ?? <p className="text-center text-sm text-muted">Authentication</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
