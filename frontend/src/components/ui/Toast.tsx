import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Info, X, XCircle } from "lucide-react";
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
  success: "border-emerald-200 bg-emerald-50 text-success",
  error: "border-red-200 bg-red-50 text-error",
  info: "border-border-light bg-card text-foreground",
};

const variantIcons: Record<ToastVariant, typeof Info> = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
};

function ToastViewport({ messages, onDismiss }: { messages: ToastMessage[]; onDismiss: (id: string) => void }) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-full max-w-sm flex-col gap-2">
      <AnimatePresence>
        {messages.map((message) => {
          const Icon = variantIcons[message.variant];
          return (
            <motion.div
              key={message.id}
              role="status"
              initial={{ opacity: 0, x: 24, scale: 0.96 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 24, scale: 0.96 }}
              transition={{ duration: 0.25 }}
              className={cn(
                "pointer-events-auto flex items-start gap-3 rounded-lg border px-4 py-3 text-sm shadow-card-md",
                variantClasses[message.variant],
              )}
            >
              <Icon className="mt-0.5 h-4 w-4 shrink-0 opacity-80" aria-hidden />
              <p className="flex-1">{message.title}</p>
              <button
                type="button"
                className="rounded-md p-0.5 opacity-70 transition-opacity hover:opacity-100"
                onClick={() => onDismiss(message.id)}
                aria-label="Dismiss notification"
              >
                <X className="h-3.5 w-3.5" aria-hidden />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
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
