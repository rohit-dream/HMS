export interface BreadcrumbItem {
  label: string;
  href?: string;
}

const LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  patients: "Patients",
  admin: "Administration",
  settings: "Hospital Settings",
  branches: "Branches",
  departments: "Departments",
  staff: "Staff",
  doctors: "Doctors",
  schedule: "Schedule",
  users: "Users",
  new: "New",
  opd: "Outpatient",
  queue: "Queue",
  appointments: "Appointments",
  billing: "Billing",
  collection: "Collection",
  ipd: "Inpatient",
  admissions: "Admissions",
  pharmacy: "Pharmacy",
  lab: "Laboratory",
  orders: "Orders",
};

export function breadcrumbsFromPath(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) {
    return [{ label: "Dashboard", href: "/dashboard" }];
  }

  const items: BreadcrumbItem[] = [];
  let path = "";

  segments.forEach((segment, index) => {
    path += `/${segment}`;
    const isLast = index === segments.length - 1;
    const isUuid =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment);

    if (isUuid) {
      items.push({ label: "Details" });
      return;
    }

    const label = LABELS[segment] ?? segment.replace(/-/g, " ");
    items.push({
      label: label.charAt(0).toUpperCase() + label.slice(1),
      href: isLast ? undefined : path,
    });
  });

  return items;
}
