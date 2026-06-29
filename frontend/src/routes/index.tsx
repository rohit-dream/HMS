import { createBrowserRouter, Navigate } from "react-router-dom";
import { PermissionRoute } from "@/components/auth/PermissionRoute";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { PublicRoute } from "@/components/auth/PublicRoute";
import { RoleRedirect } from "@/components/auth/RoleRedirect";
import { AppLayout } from "@/components/layout/AppLayout";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { AcceptInvitePage } from "@/pages/AcceptInvitePage";
import { AppointmentCalendarPage } from "@/pages/appointments/AppointmentCalendarPage";
import { AppointmentDetailPage } from "@/pages/appointments/AppointmentDetailPage";
import { BranchesPage } from "@/pages/admin/BranchesPage";
import { DepartmentsPage } from "@/pages/admin/DepartmentsPage";
import { DoctorFormPage } from "@/pages/admin/DoctorFormPage";
import { DoctorSchedulePage } from "@/pages/admin/DoctorSchedulePage";
import { DoctorsPage } from "@/pages/admin/DoctorsPage";
import { HealthStatusPage } from "@/pages/admin/HealthStatusPage";
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
import { OpdConsultationPage } from "@/pages/opd/OpdConsultationPage";
import { OpdQueueBoardPage } from "@/pages/opd/OpdQueueBoardPage";
import { OpdVisitSummaryPage } from "@/pages/opd/OpdVisitSummaryPage";
import { PatientListPage } from "@/pages/patients/PatientListPage";
import { PatientProfilePage } from "@/pages/patients/PatientProfilePage";
import { PatientRegistrationPage } from "@/pages/patients/PatientRegistrationPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { VerifyEmailPage } from "@/pages/VerifyEmailPage";

import { Link } from "react-router-dom";
import { GlassCard } from "@/components/ui/GlassCard";
import { PageShell } from "@/components/ui/PageShell";

function NotFoundPage() {
  return (
    <PageShell>
      <GlassCard strong padding="lg" className="text-center">
        <h2 className="text-xl font-semibold text-foreground">404 — Page not found</h2>
        <p className="mt-2 text-sm text-muted">The page you requested does not exist.</p>
        <Link
          to="/dashboard"
          className="mt-6 inline-flex text-sm text-primary transition-colors hover:text-accent hover:underline"
        >
          Go to dashboard
        </Link>
      </GlassCard>
    </PageShell>
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
    path: "/accept-invite",
    element: (
      <PublicRoute>
        <AuthLayout>
          <AcceptInvitePage />
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
        path: "patients",
        element: (
          <PermissionRoute permission="patient:read">
            <PatientListPage />
          </PermissionRoute>
        ),
      },
      {
        path: "patients/new",
        element: (
          <PermissionRoute permission="patient:create">
            <PatientRegistrationPage />
          </PermissionRoute>
        ),
      },
      {
        path: "patients/:patientId",
        element: (
          <PermissionRoute permission="patient:read">
            <PatientProfilePage />
          </PermissionRoute>
        ),
      },
      {
        path: "appointments",
        element: (
          <PermissionRoute permission="appointment:read">
            <AppointmentCalendarPage />
          </PermissionRoute>
        ),
      },
      {
        path: "appointments/:appointmentId",
        element: (
          <PermissionRoute permission="appointment:read">
            <AppointmentDetailPage />
          </PermissionRoute>
        ),
      },
      {
        path: "opd/queue",
        element: (
          <PermissionRoute permission="opd:read">
            <OpdQueueBoardPage />
          </PermissionRoute>
        ),
      },
      {
        path: "opd/consult/:visitId",
        element: (
          <PermissionRoute permission="opd:consult">
            <OpdConsultationPage />
          </PermissionRoute>
        ),
      },
      {
        path: "opd/visits/:visitId",
        element: (
          <PermissionRoute permission="opd:read">
            <OpdVisitSummaryPage />
          </PermissionRoute>
        ),
      },
      {
        path: "opd/appointments",
        element: <Navigate to="/appointments" replace />,
      },
      {
        path: "ipd/admissions",
        element: (
          <PermissionRoute permission="ipd:read">
            <ModulePlaceholderPage
              title="IPD Admissions"
              description="Admitted patients and ward management will be built in the IPD sprint."
            />
          </PermissionRoute>
        ),
      },
      {
        path: "billing/collection",
        element: (
          <PermissionRoute permission="billing:read">
            <ModulePlaceholderPage
              title="Daily Collection"
              description="Billing and collection views will be built in the billing sprint."
            />
          </PermissionRoute>
        ),
      },
      {
        path: "pharmacy/queue",
        element: (
          <PermissionRoute permission="pharmacy:read">
            <ModulePlaceholderPage
              title="Pharmacy Queue"
              description="Prescription dispensing queue will be built in the pharmacy sprint."
            />
          </PermissionRoute>
        ),
      },
      {
        path: "lab/orders",
        element: (
          <PermissionRoute permission="laboratory:read">
            <ModulePlaceholderPage
              title="Lab Orders"
              description="Laboratory order queue will be built in the lab sprint."
            />
          </PermissionRoute>
        ),
      },
      {
        path: "admin/health",
        element: (
          <PermissionRoute permission="admin:settings">
            <HealthStatusPage />
          </PermissionRoute>
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
