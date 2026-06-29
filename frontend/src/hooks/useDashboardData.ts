import { useQueries } from "@tanstack/react-query";
import { searchUsersRequest } from "@/api/endpoints/admin-users";
import { listDepartmentsRequest } from "@/api/endpoints/departments";
import { listDoctorsRequest } from "@/api/endpoints/doctors";
import { getHospitalProfileRequest, listLocationsRequest } from "@/api/endpoints/hospital";
import { listStaffRequest } from "@/api/endpoints/staff";
import { listPatientsRequest } from "@/api/endpoints/patients";
import { usePermissions } from "@/hooks/usePermissions";

export function useDashboardData() {
  const { hasPermission } = usePermissions();

  const results = useQueries({
    queries: [
      {
        queryKey: ["dashboard", "hospital-profile"],
        queryFn: getHospitalProfileRequest,
      },
      {
        queryKey: ["dashboard", "locations"],
        queryFn: listLocationsRequest,
      },
      {
        queryKey: ["dashboard", "users-count"],
        queryFn: () => searchUsersRequest({ page: 1, page_size: 1 }),
        enabled: hasPermission("admin:users"),
      },
      {
        queryKey: ["dashboard", "departments-count"],
        queryFn: () => listDepartmentsRequest({ page: 1, page_size: 1 }),
        enabled: hasPermission("admin:departments"),
      },
      {
        queryKey: ["dashboard", "staff-count"],
        queryFn: () => listStaffRequest({ page: 1, page_size: 1, status: "active" }),
        enabled: hasPermission("admin:staff"),
      },
      {
        queryKey: ["dashboard", "doctors-count"],
        queryFn: () => listDoctorsRequest({ page: 1, page_size: 1 }),
        enabled: hasPermission("admin:doctors"),
      },
      {
        queryKey: ["dashboard", "doctors-available"],
        queryFn: () => listDoctorsRequest({ page: 1, page_size: 100 }),
        enabled: hasPermission("admin:doctors"),
      },
      {
        queryKey: ["dashboard", "recent-users"],
        queryFn: () => searchUsersRequest({ page: 1, page_size: 8 }),
        enabled: hasPermission("admin:users"),
      },
      {
        queryKey: ["dashboard", "patients-count"],
        queryFn: () => listPatientsRequest({ page: 1, page_size: 1 }),
        enabled: hasPermission("patient:read"),
      },
    ],
  });

  const [
    profileQuery,
    locationsQuery,
    usersCountQuery,
    departmentsCountQuery,
    staffCountQuery,
    doctorsCountQuery,
    doctorsListQuery,
    recentUsersQuery,
    patientsCountQuery,
  ] = results;

  const doctors = doctorsListQuery.data?.data ?? [];
  const availableDoctors = doctors.filter((doctor) => doctor.is_available).length;

  const isLoading = results.some((query) => query.isLoading);

  return {
    isLoading,
    hospital: profileQuery.data ?? null,
    branchCount: locationsQuery.data?.length ?? 0,
    primaryBranch: locationsQuery.data?.find((location) => location.is_primary) ?? null,
    userCount: usersCountQuery.data?.pagination?.total_items,
    departmentCount: departmentsCountQuery.data?.pagination?.total_items,
    staffCount: staffCountQuery.data?.pagination?.total_items,
    doctorCount: doctorsCountQuery.data?.pagination?.total_items,
    availableDoctors,
    recentUsers: recentUsersQuery.data?.data ?? [],
    patientCount: patientsCountQuery.data?.pagination?.total_items,
    canViewUsers: hasPermission("admin:users"),
    canViewPatients: hasPermission("patient:read"),
    canViewDepartments: hasPermission("admin:departments"),
    canViewStaff: hasPermission("admin:staff"),
    canViewDoctors: hasPermission("admin:doctors"),
  };
}
