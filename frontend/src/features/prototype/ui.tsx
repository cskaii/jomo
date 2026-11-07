"use client";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { message } from "@/services/prototype";
import { cachedResource, clearResourceCache, fetchResource } from "@/lib/resourceCache";
import { sessionOwner } from "@/services/authSession";
import { PageLoading } from "@/components/common/PageLoading";
export function useResource<T>(load: () => Promise<T>, cacheKey?: string) {
  const key = cacheKey ?? load;
  const owner = typeof window === "undefined" ? "" : sessionOwner(localStorage.getItem("jomo_auth_token"));
  const [state, setState] = useState<{
    data?: T;
    error?: string;
    load?: typeof load;
    revision?: number;
    owner?: string;
    key?: typeof key;
  }>({});
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  useEffect(() => {
    let current = true;
    fetchResource(key, load, owner, revision > 0)
      .then((data) => {
        if (current && owner === sessionOwner(localStorage.getItem("jomo_auth_token")))
          setState({ data, load, revision, owner, key });
      })
      .catch((error: unknown) => {
        if (current) setState(previous => ({
          data: previous.owner === owner && previous.key === key ? previous.data : undefined,
          error: message(error), load, revision, owner, key,
        }));
      });
    return () => {
      current = false;
    };
  }, [load, revision, key, owner]);
  useEffect(() => {
    const changed = (event: StorageEvent) => {
      if (event.key === "jomo_auth_token") {
        clearResourceCache();
        refresh();
      }
    };
    window.addEventListener("storage", changed);
    return () => window.removeEventListener("storage", changed);
  }, [refresh]);
  const current = state.load === load && state.revision === revision && state.owner === owner;
  const cached = cachedResource<T>(key, owner);
  const data = state.owner === owner && state.key === key ? state.data ?? cached : cached;
  return {
    data,
    error: current ? state.error : undefined,
    loading: !current && data === undefined,
    refreshing: !current,
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
    return <PageLoading />;
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
  disabled = false,
}: {
  pending: boolean;
  children: ReactNode;
  disabled?: boolean;
}) {
  return (
    <button
      className="j-button"
      type="submit"
      disabled={pending || disabled}
      aria-busy={pending}
    >
      {pending ? "Please wait…" : children}
    </button>
  );
}
