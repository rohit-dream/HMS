import {
  ClinicalModulesPanel,
  DashboardWelcome,
  HospitalKpiGrid,
  QuickActionsPanel,
} from "@/components/dashboard/DashboardSections";
import {
  AlertsPanel,
  DoctorAvailabilityPanel,
  RecentActivityPanel,
} from "@/components/dashboard/DashboardPanels";

export function HomePage() {
  return (
    <div className="mx-auto w-full max-w-[90rem] space-y-8 animate-fade-in">
      <DashboardWelcome />

      <HospitalKpiGrid />

      <DoctorAvailabilityPanel />

      <div className="grid gap-6 xl:grid-cols-12">
        <div className="space-y-6 xl:col-span-7">
          <ClinicalModulesPanel />
          <RecentActivityPanel />
        </div>
        <div className="space-y-6 xl:col-span-5">
          <QuickActionsPanel />
          <AlertsPanel />
        </div>
      </div>
    </div>
  );
}
