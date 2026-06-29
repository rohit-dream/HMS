import { Outlet } from "react-router-dom";
import { SessionIdleMonitor } from "@/components/auth/SessionIdleMonitor";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { SidebarProvider } from "./SidebarContext";

export function AppLayout() {
  return (
    <SidebarProvider>
      <div className="min-h-screen bg-surface">
        <SessionIdleMonitor />

        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <Header />
            <main className="flex-1 bg-surface px-4 py-6 sm:px-6 sm:py-8">
              <Outlet />
            </main>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
}
