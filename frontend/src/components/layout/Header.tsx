import { useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Bell, ChevronRight, LogOut, Menu, Settings, User } from "lucide-react";
import { getHospitalProfileRequest } from "@/api/endpoints/hospital";
import { useSidebar } from "@/components/layout/SidebarContext";
import { Button } from "@/components/ui/Button";
import { breadcrumbsFromPath } from "@/lib/breadcrumbs";
import { useAuth } from "@/providers/AuthProvider";
import { cn } from "@/lib/cn";

export function Header() {
  const { user, logout } = useAuth();
  const { setMobileOpen } = useSidebar();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const profileQuery = useQuery({
    queryKey: ["hospital", "profile", "header"],
    queryFn: getHospitalProfileRequest,
  });

  const crumbs = useMemo(() => breadcrumbsFromPath(location.pathname), [location.pathname]);
  const hospitalName = profileQuery.data?.name ?? "Hospital Management System";

  return (
    <header className="glass-header sticky top-0 z-30">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            className="rounded-lg p-2 text-muted transition-colors hover:bg-hover lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="min-w-0">
            <p className="truncate text-xs font-medium uppercase tracking-wide text-muted">
              {hospitalName}
            </p>
            <nav aria-label="Breadcrumb" className="mt-0.5 flex flex-wrap items-center gap-1 text-sm">
              {crumbs.map((crumb, index) => (
                <span key={`${crumb.label}-${index}`} className="inline-flex items-center gap-1">
                  {index > 0 && <ChevronRight className="h-3.5 w-3.5 text-border" aria-hidden />}
                  {crumb.href ? (
                    <Link to={crumb.href} className="truncate text-muted transition-colors hover:text-foreground">
                      {crumb.label}
                    </Link>
                  ) : (
                    <span className="truncate font-medium text-foreground">{crumb.label}</span>
                  )}
                </span>
              ))}
            </nav>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="hidden rounded-lg border border-border-light p-2 text-muted transition-colors hover:bg-hover sm:inline-flex"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" />
          </button>

          <div className="relative">
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              className={cn(
                "flex items-center gap-2 rounded-lg border border-border-light bg-card py-1.5 pl-1.5 pr-3 transition-colors hover:bg-hover",
                menuOpen && "bg-hover",
              )}
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-xs font-semibold text-white">
                {user?.first_name?.charAt(0) ?? "U"}
              </span>
              <span className="hidden max-w-[10rem] truncate text-left text-sm sm:block">
                <span className="block font-medium text-foreground">
                  {user ? `${user.first_name} ${user.last_name}` : "User"}
                </span>
                <span className="block truncate text-xs text-muted">{user?.email}</span>
              </span>
            </button>

            {menuOpen && (
              <>
                <button
                  type="button"
                  className="fixed inset-0 z-40 cursor-default"
                  aria-label="Close user menu"
                  onClick={() => setMenuOpen(false)}
                />
                <div className="absolute right-0 z-50 mt-2 w-56 overflow-hidden rounded-xl border border-border-light bg-card p-2 shadow-card-md">
                  <Link
                    to="/admin/settings"
                    className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-hover"
                    onClick={() => setMenuOpen(false)}
                  >
                    <Settings className="h-4 w-4" />
                    Hospital settings
                  </Link>
                  <Link
                    to="/admin/users"
                    className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-hover"
                    onClick={() => setMenuOpen(false)}
                  >
                    <User className="h-4 w-4" />
                    User management
                  </Link>
                  <div className="my-1 border-t border-border-light" />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={() => {
                      setMenuOpen(false);
                      void logout();
                    }}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign out
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
