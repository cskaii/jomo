"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { request, profile, success, z } from "@/services/prototype";
import { apiClient } from "@/services/apiClient";
import { authSession, clearSession, saveSession } from "@/services/authSession";
import { useAction, Feedback, Panel, Heading, Submit } from "./ui";
import { LoadingScene } from "@/components/common/LoadingScene";
import { welcomeTitle } from "@/lib/loadingCopy";
import { fetchResource } from "@/lib/resourceCache";
import { sessionOwner } from "@/services/authSession";
import { NewPasswordField, useNewPasswordAssessment } from "./NewPasswordField";

export default function Login() { return <AccountForm registration={false} />; }
export function Register() { return <AccountForm registration />; }
function AccountForm({ registration }: { registration: boolean }) {
  const router = useRouter(), action = useAction();
  const [email, setEmail] = useState(""), [password, setPassword] = useState("");
  const strength = useNewPasswordAssessment(password, email, registration);
  const [welcomeProfile, setWelcomeProfile] = useState<z.infer<typeof profile> | null>(null);
  const [entered, setEntered] = useState(false);
  useEffect(() => {
    // Email confirmation may return an implicit-flow fragment. Do not retain it
    // in browser history; the account signs in through the verified password flow.
    if (window.location.hash) window.history.replaceState(null, "", window.location.pathname);
  }, []);
  async function openSession(session: z.infer<typeof authSession>) {
    saveSession(session);
    try {
      const me = await request(profile, "/users/me");
      setWelcomeProfile(me);
      await fetchResource("account-profile", async () => me, sessionOwner(session.access_token));
      setEntered(true);
      router.replace("/insights");
      } catch (error) { setEntered(false); throw error; }
  }
  if (action.pending || entered) return <LoadingScene variant="welcome"
    title={registration && !entered ? "A little room to grow." : welcomeTitle(registration, welcomeProfile?.display_name, welcomeProfile?.username)}
    description={entered ? "Preparing your little space…" : registration ? "Creating your JOMO account…" : "Opening your little space…"} />;
  return <div className="j-auth">
    <Heading eyebrow="JOMO" title={registration ? "A little room to grow." : "Welcome back."}><p>Less scrolling. More living.</p></Heading>
    <Panel title={registration ? "Create your account" : "Sign in to your garden"}>
      <form className="j-form" onSubmit={event => {
        event.preventDefault();
        void action.run(async () => {
          const input = { email: z.email().parse(email.trim()), password };
          if (registration) {
            if (!strength?.accepted) throw new Error("Choose a password rated Strong or Very strong before creating your account.");
            const result = await request(z.object({ session: authSession.nullable(), message: z.string() }), "/auth/register", "post", input);
            setPassword("");
            if (result.session) await openSession(result.session);
          } else {
            const session = await request(authSession, "/auth/login", "post", input);
            setPassword("");
            await openSession(session);
          }
        }, registration ? "Check your email to confirm your account, then sign in." : "");
      }}>
        <label>Email<input type="email" required autoComplete="email" maxLength={254} value={email} onChange={event => setEmail(event.target.value)} /></label>
        {registration ? <NewPasswordField value={password} onChange={setPassword} assessment={strength} /> :
          <label>Password<input name="password" type="password" required minLength={1} maxLength={1024} autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} /></label>}
        <Submit pending={action.pending} disabled={registration && !strength?.accepted}>{registration ? "Create account" : "Sign in"}</Submit>
        <Feedback action={action} />
      </form>
      {registration && <p>Creating an account asks JOMO to process your account and activity data for this service. Location and photos are optional. <Link href="/privacy">Read the privacy notice</Link>.</p>}
      <p>{registration ? <Link href="/login">Already have an account? Sign in</Link> : <Link href="/register">Create an account</Link>}</p>
      {!registration && <Link href="/forgot-password">Forgot your password?</Link>}
      {!registration && process.env.NEXT_PUBLIC_DEV_AUTH_ENABLED === "true" && <div className="j-form">
        <p>Local preview: explore with a new account on this computer.</p>
        <button type="button" className="j-button secondary" disabled={action.pending} onClick={() => void action.run(async () => {
          const session = await request(authSession, "/auth/dev-session", "post");
          await openSession(session);
        })}>Open local preview</button>
      </div>}
    </Panel>
  </div>;
}

export function ForgotPassword() {
  const action = useAction();
  const [email, setEmail] = useState("");
  return <div className="j-auth"><Heading eyebrow="JOMO" title="Find your way back." />
    <Panel title="Reset your password"><form className="j-form" onSubmit={event => {
      event.preventDefault();
      void action.run(async () => { await request(success, "/auth/recover", "post", {email: z.email().parse(email.trim())}); }, "If this email can receive recovery messages, a reset link has been sent.");
    }}><label>Email<input type="email" required autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} /></label><Submit pending={action.pending}>Send reset link</Submit><Feedback action={action} /></form><p><Link href="/login">Back to sign in</Link></p></Panel>
  </div>;
}

export function ResetPassword() {
  const action = useAction();
  const [token, setToken] = useState(""), [password, setPassword] = useState("");
  const strength = useNewPasswordAssessment(password);
  useEffect(() => {
    const fragment = new URLSearchParams(window.location.hash.slice(1));
    const recoveryToken = fragment.get("type") === "recovery" ? fragment.get("access_token") || "" : "";
    // Read the external URL once after hydration and erase its sensitive fragment.
    const update = window.setTimeout(() => setToken(recoveryToken), 0);
    window.history.replaceState(null, "", window.location.pathname);
    return () => window.clearTimeout(update);
  }, []);
  return <div className="j-auth"><Heading eyebrow="JOMO" title="A fresh start." /><Panel title="Choose a new password">
    {!token ? <p>Open the reset link from your email. If it expired, <Link href="/forgot-password">request another link</Link>.</p> :
      <form className="j-form" onSubmit={event => {
        event.preventDefault();
        void action.run(async () => {
          if (!strength?.accepted) throw new Error("Choose a password rated Strong or Very strong before saving.");
          const response = await apiClient.post("/auth/password", { password }, { headers: { Authorization: `Bearer ${token}` } });
          success.parse(response.data.data);
          setPassword(""); setToken(""); clearSession();
        }, "Password updated. You can sign in now.");
      }}><NewPasswordField label="New password" value={password} onChange={setPassword} assessment={strength} /><Submit pending={action.pending} disabled={!strength?.accepted}>Update password</Submit></form>}
    <Feedback action={action} /><p><Link href="/login">Back to sign in</Link></p>
  </Panel></div>;
}
