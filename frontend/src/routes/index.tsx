import { createBrowserRouter, Navigate } from "react-router-dom";
import { PermissionRoute } from "@/components/auth/PermissionRoute";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { PublicRoute } from "@/components/auth/PublicRoute";
import { RoleRedirect } from "@/components/auth/RoleRedirect";
import { AppLayout } from "@/components/layout/AppLayout";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { BranchesPage } from "@/pages/admin/BranchesPage";
import { DepartmentsPage } from "@/pages/admin/DepartmentsPage";
import { DoctorFormPage } from "@/pages/admin/DoctorFormPage";
import { DoctorSchedulePage } from "@/pages/admin/DoctorSchedulePage";
import { DoctorsPage } from "@/pages/admin/DoctorsPage";
import { HospitalSettingsPage } from "@/pages/admin/HospitalSettingsPage";
import { StaffFormPage } from "@/pages/admin/StaffFormPage";
import { StaffPage } from "@/pages/admin/StaffPage";
import { UserDetailPage } from "@/pages/admin/UserDetailPage";
import { UsersPage } from "@/pages/admin/UsersPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { LegalPrivacyPage } from "@/pages/LegalPrivacyPage";
import { LegalTermsPage } from "@/pages/LegalTermsPage";
import { LoginPage } from "@/pages/LoginPage";
import { ModulePlaceholderPage } from "@/pages/ModulePlaceholderPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { VerifyEmailPage } from "@/pages/VerifyEmailPage";

function NotFoundPage() {
  return (
    <div className="rounded-lg border border-border bg-white p-8 text-center">
      <h2 className="text-xl font-semibold">404 — Page not found</h2>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/register",
    element: (
      <PublicRoute>
        <AuthLayout wide>
          <RegisterPage />
        </AuthLayout>
      </PublicRoute>
    ),
  },
  {
    path: "/legal/terms",
    element: (
      <AuthLayout wide>
        <LegalTermsPage />
      </AuthLayout>
    ),
  },
  {
    path: "/legal/privacy",
    element: (
      <AuthLayout wide>
        <LegalPrivacyPage />
      </AuthLayout>
    ),
  },
  {
    path: "/login",
    element: (
      <PublicRoute>
        <AuthLayout>
          <LoginPage />
        </AuthLayout>
      </PublicRoute>
    ),
  },
  {
    path: "/forgot-password",
    element: (
      <PublicRoute>
        <AuthLayout>
          <ForgotPasswordPage />
        </AuthLayout>
      </PublicRoute>
    ),
  },
  {
    path: "/reset-password",
    element: (
      <PublicRoute>
        <AuthLayout>
          <ResetPasswordPage />
        </AuthLayout>
      </PublicRoute>
    ),
  },
  {
    path: "/verify-email",
    element: (
      <AuthLayout>
        <VerifyEmailPage />
      </AuthLayout>
    ),
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <RoleRedirect /> },
      { path: "dashboard", element: <DashboardPage /> },
      {
        path: "opd/queue",
        element: (
          <ModulePlaceholderPage
            title="OPD Queue"
            description="Today's OPD queue board will be built in the OPD sprint."
          />
        ),
      },
      {
        path: "opd/appointments",
        element: (
          <ModulePlaceholderPage
            title="Appointments"
            description="Appointment calendar and scheduling will be built in the OPD sprint."
          />
        ),
      },
      {
        path: "ipd/admissions",
        element: (
          <ModulePlaceholderPage
            title="IPD Admissions"
            description="Admitted patients and ward management will be built in the IPD sprint."
          />
        ),
      },
      {
        path: "billing/collection",
        element: (
          <ModulePlaceholderPage
            title="Daily Collection"
            description="Billing and collection views will be built in the billing sprint."
          />
        ),
      },
      {
        path: "pharmacy/queue",
        element: (
          <ModulePlaceholderPage
            title="Pharmacy Queue"
            description="Prescription dispensing queue will be built in the pharmacy sprint."
          />
        ),
      },
      {
        path: "lab/orders",
        element: (
          <ModulePlaceholderPage
            title="Lab Orders"
            description="Laboratory order queue will be built in the lab sprint."
          />
        ),
      },
      {
        path: "admin/settings",
        element: (
          <PermissionRoute permission="admin:settings">
            <HospitalSettingsPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/branches",
        element: (
          <PermissionRoute permission="admin:settings">
            <BranchesPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/departments",
        element: (
          <PermissionRoute permission="admin:departments">
            <DepartmentsPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/staff",
        element: (
          <PermissionRoute permission="admin:staff">
            <StaffPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/staff/new",
        element: (
          <PermissionRoute permission="admin:staff">
            <StaffFormPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/staff/:staffId",
        element: (
          <PermissionRoute permission="admin:staff">
            <StaffFormPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/doctors",
        element: (
          <PermissionRoute permission="admin:doctors">
            <DoctorsPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/doctors/new",
        element: (
          <PermissionRoute permission="admin:doctors">
            <DoctorFormPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/doctors/:doctorId/schedule",
        element: (
          <PermissionRoute permission="admin:doctors">
            <DoctorSchedulePage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/doctors/:doctorId",
        element: (
          <PermissionRoute permission="admin:doctors">
            <DoctorFormPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/users",
        element: (
          <PermissionRoute permission="admin:users">
            <UsersPage />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/users/:userId",
        element: (
          <PermissionRoute permission="admin:users">
            <UserDetailPage />
          </PermissionRoute>
        ),
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
