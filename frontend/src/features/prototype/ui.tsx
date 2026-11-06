"use client";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { message } from "@/services/prototype";
export function useResource<T>(load: () => Promise<T>) {
  const [state, setState] = useState<{
    data?: T;
    error?: string;
    load?: typeof load;
    revision?: number;
  }>({});
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  useEffect(() => {
    let current = true;
    load()
      .then((data) => {
        if (current) setState({ data, load, revision });
      })
      .catch((error: unknown) => {
        if (current) setState({ error: message(error), load, revision });
      });
    return () => {
      current = false;
    };
  }, [load, revision]);
  const current = state.load === load && state.revision === revision;
  return {
    data: current ? state.data : undefined,
    error: current ? state.error : undefined,
    loading: !current,
    refresh,
  };
}
export function useAction() {
  const lock = useRef(false);
  const [pending, setPending] = useState(false),
    [notice, setNotice] = useState(""),
    [error, setError] = useState("");
  async function run(work: () => Promise<void>, success = "") {
    if (lock.current) return;
    lock.current = true;
    setPending(true);
    setError("");
    setNotice("");
    try {
      await work();
      setNotice(success);
    } catch (cause: unknown) {
      setError(message(cause));
    } finally {
      lock.current = false;
      setPending(false);
    }
  }
  return { run, pending, notice, error };
}
export function Feedback({ action }: { action: ReturnType<typeof useAction> }) {
  return (
    <>
      {action.error && (
        <p role="alert" className="j-error">
          {action.error}
        </p>
      )}
      {action.notice && (
        <p role="status" className="j-notice">
          {action.notice}
        </p>
      )}
    </>
  );
}
export function ResourceState({
  loading,
  error,
  retry,
}: {
  loading: boolean;
  error?: string;
  retry: () => void;
}) {
  if (loading)
    return (
      <p role="status" className="j-panel">
        Growing your view…
      </p>
    );
  if (error)
    return (
      <div role="alert" className="j-panel j-error">
        <p>{error}</p>
        <button className="j-button" onClick={retry}>
          Try again
        </button>
      </div>
    );
  return null;
}
export function Heading({
  eyebrow,
  title,
  children,
  level = 1,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
  level?: 1 | 2;
}) {
  const Title = level === 2 ? "h2" : "h1";
  return (
    <div className="j-heading">
      <p className="j-eyebrow">{eyebrow}</p>
      <Title>{title}</Title>
      {children}
    </div>
  );
}
export function Panel({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`j-panel ${className}`}>
      {title && <h2>{title}</h2>}
      {children}
    </section>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return <p className="j-empty">{children}</p>;
}
export function Submit({
  pending,
  children,
}: {
  pending: boolean;
  children: ReactNode;
}) {
  return (
    <button
      className="j-button"
      type="submit"
      disabled={pending}
      aria-busy={pending}
    >
      {pending ? "Please wait…" : children}
    </button>
  );
}
