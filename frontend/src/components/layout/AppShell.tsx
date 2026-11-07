"use client";
import { useEffect, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Leaf,
  Users,
  Flower2,
  ShieldCheck,
  LogOut,
} from "lucide-react";
import { profile, request } from "@/services/prototype";
import { signOut } from "@/services/authSession";
import { useResource } from "@/features/prototype/ui";
import { EvilDuckGame } from "@/features/privacy-game/EvilDuckGame";
const links = [
  ["/insights", "Insights", Leaf],
  ["/garden", "Garden", Flower2],
  ["/friends", "Friends", Users],
] as const;
async function loadProfile() {
  if (!localStorage.getItem("jomo_auth_token"))
    throw new Error("Sign in to open your space.");
  return request(profile, "/users/me");
}
export function AppShell({ children }: { children: ReactNode }) {
  const path = usePathname(),
    router = useRouter(),
    account = useResource(loadProfile, "account-profile");
  useEffect(() => {
    if (!localStorage.getItem("jomo_auth_token")) router.replace("/login");
    const expired = () => router.replace("/login");
    const storage = (event: StorageEvent) => {
      if (event.key === "jomo_auth_token" && !event.newValue) expired();
    };
    window.addEventListener("jomo:session-expired", expired);
    window.addEventListener("storage", storage);
    return () => {
      window.removeEventListener("jomo:session-expired", expired);
      window.removeEventListener("storage", storage);
    };
  }, [router]);
  async function logout() {
    try { await signOut(); } catch { /* Local credentials are cleared even offline. */ }
    router.replace("/login");
    router.refresh();
  }
  function active(href: string) {
    return (
      (path.startsWith(href) &&
        !(href === "/friends" && path.startsWith("/friends/groups"))) ||
      (href === "/garden" && (path.startsWith("/friends/groups") || path.startsWith("/activities") || path.startsWith("/focus")))
    );
  }
  return (
    <div className={`j-app ${path === "/insights" ? "j-today-app" : ""}`}>
      <a className="j-skip" href="#main">
        Skip to content
      </a>
      <header className="j-site-header">
        <div className="j-header-inner">
          <Link className="j-wordmark" href="/insights" aria-label="JOMO home">
            <span className="j-brand-mark">
              <Leaf aria-hidden="true" />
            </span>
            JOMO
          </Link>
          <nav className="j-desktop-nav" aria-label="Main navigation">
            {links.map(([href, label, Icon]) => (
              <Link
                key={href}
                href={href}
                aria-current={active(href) ? "page" : undefined}
              >
                <Icon aria-hidden="true" />
                {label}
              </Link>
            ))}
          </nav>
          <div className="j-account">
            <Link className="j-account-name" href="/settings">
              <strong>{account.data?.display_name ?? "Your space"}</strong>
              <span>LESS SCROLLING. MORE LIVING.</span>
            </Link>
            <Link
              className="j-avatar"
              href="/settings"
              aria-label="Account settings"
            >
              {account.data?.display_name.slice(0, 1).toUpperCase() ?? "·"}
            </Link>
            <Link
              className="j-icon-button"
              href="/privacy-guardian"
              aria-label="Privacy Guardian"
              title="Privacy Guardian"
            >
              <ShieldCheck aria-hidden="true" />
            </Link>
            <button
              className="j-icon-button"
              onClick={logout}
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>
      <main id="main" tabIndex={-1} className="j-main">
        {account.error && <div className="j-panel j-error" role="alert">
          <p>{account.error}</p>
          <button className="j-button" onClick={account.refresh}>Retry connection</button>
          <Link href="/login">Sign in</Link>
        </div>}
        {children}
      </main>
      {account.data && <EvilDuckGame key={account.data.id} userId={account.data.id} />}
      <footer className="j-footer">
        <span>
          <Leaf aria-hidden="true" /> A little less online. A little more here.
        </span>
        <div>
          <span className="j-prototype-label">Local prototype</span>
          <Link href="/privacy-guardian">Privacy Guardian</Link>
          <Link href="/settings">Your preferences</Link>
        </div>
      </footer>
      <nav className="j-bottom" aria-label="Mobile navigation">
        {links.map(([href, label, Icon]) => (
          <Link
            key={href}
            href={href}
            aria-current={active(href) ? "page" : undefined}
          >
            <Icon aria-hidden="true" />
            {label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
