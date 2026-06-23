import { useAuth } from "@/providers/AuthProvider";
import { APP_NAME } from "@/lib/constants";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between border-b border-border bg-white px-6 py-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">{APP_NAME}</h1>
        <p className="text-sm text-muted">
          {user ? `Signed in as ${user.email}` : "Hospital management workspace"}
        </p>
      </div>
      {user ? (
        <button
          type="button"
          onClick={() => void logout()}
          className="rounded-lg border border-border px-3 py-1.5 text-sm text-slate-700 hover:bg-surface"
        >
          Sign out
        </button>
      ) : (
        <div className="rounded-full bg-surface px-3 py-1 text-sm text-muted">Guest</div>
      )}
    </header>
  );
}
