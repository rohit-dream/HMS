import { Outlet } from "react-router-dom";
import { SessionIdleMonitor } from "@/components/auth/SessionIdleMonitor";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-surface">
      <SessionIdleMonitor />
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
