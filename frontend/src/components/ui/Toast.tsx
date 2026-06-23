import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { cn } from "@/lib/cn";

export type ToastVariant = "success" | "error" | "info";

export interface ToastMessage {
  id: string;
  title: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toast: (input: { title: string; variant?: ToastVariant }) => void;
  success: (title: string) => void;
  error: (title: string) => void;
  info: (title: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const variantClasses: Record<ToastVariant, string> = {
  success: "border-green-200 bg-green-50 text-success",
  error: "border-red-200 bg-red-50 text-error",
  info: "border-border bg-white text-slate-900",
};

function ToastViewport({ messages, onDismiss }: { messages: ToastMessage[]; onDismiss: (id: string) => void }) {
  if (messages.length === 0) return null;

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-full max-w-sm flex-col gap-2">
      {messages.map((message) => (
        <div
          key={message.id}
          role="status"
          className={cn(
            "pointer-events-auto rounded-lg border px-4 py-3 text-sm shadow-md",
            variantClasses[message.variant],
          )}
        >
          <div className="flex items-start justify-between gap-3">
            <p>{message.title}</p>
            <button
              type="button"
              className="text-xs opacity-70 hover:opacity-100"
              onClick={() => onDismiss(message.id)}
              aria-label="Dismiss notification"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  const dismiss = useCallback((id: string) => {
    setMessages((current) => current.filter((item) => item.id !== id));
  }, []);

  const push = useCallback(
    (title: string, variant: ToastVariant) => {
      const id = crypto.randomUUID();
      setMessages((current) => [...current, { id, title, variant }]);
      window.setTimeout(() => dismiss(id), 5000);
    },
    [dismiss],
  );

  const value = useMemo<ToastContextValue>(
    () => ({
      toast: ({ title, variant = "info" }) => push(title, variant),
      success: (title) => push(title, "success"),
      error: (title) => push(title, "error"),
      info: (title) => push(title, "info"),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport messages={messages} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
