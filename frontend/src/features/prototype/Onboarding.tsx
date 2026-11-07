"use client";
import { useState } from "react";
import Link from "next/link";
import { request, profile, preferences, success, z } from "@/services/prototype";
import { Panel, useAction, useResource, Feedback } from "./ui";

async function load() {
  const [me, prefs] = await Promise.all([request(profile, "/users/me"), request(preferences, "/users/me/preferences")]);
  return { me, prefs };
}
export function Onboarding() {
  const view = useResource(load, "onboarding");
  if (!view.data || view.data.prefs.onboarding_completed_at) return null;
  return <WelcomeForm initial={view.data} done={view.refresh} />;
}
function WelcomeForm({ initial, done }: { initial: Awaited<ReturnType<typeof load>>; done: () => void }) {
  const action = useAction(); const [closed, setClosed] = useState(false);
  const [name, setName] = useState(initial.me.display_name);
  const [zone, setZone] = useState(initial.prefs.timezone);
  const [goal, setGoal] = useState(String(initial.prefs.daily_screen_goal_minutes ?? 120));
  const [ack, setAck] = useState(false);
  if (closed) return null;
  return <Panel title="Make this your space">
    <p>Log your screen time in Insights. Completed activities earn coins for their personal or group garden. Location and photos are optional evidence, not automatic tracking.</p>
    <form className="j-form" onSubmit={event => { event.preventDefault(); void action.run(async () => {
      new Intl.DateTimeFormat("en", { timeZone: zone }).format();
      await request(profile, "/users/me", "patch", { display_name: z.string().trim().min(1).max(80).parse(name) });
      await request(preferences, "/users/me/preferences", "patch", { timezone: zone, daily_screen_goal_minutes: z.coerce.number().int().min(1).max(1440).parse(goal) });
      await request(success, "/users/me/onboarding", "post", { privacy_notice_acknowledged: ack });
      window.dispatchEvent(new Event("jomo:profile-updated")); done();
    }); }}>
      <label>Display name<input required maxLength={80} value={name} onChange={event => setName(event.target.value)} /></label>
      <label>Time zone<input required value={zone} onChange={event => setZone(event.target.value)} /></label>
      <label>Daily screen-time intention (minutes)<input required type="number" min={1} max={1440} value={goal} onChange={event => setGoal(event.target.value)} /></label>
      <label className="j-checkbox"><input type="checkbox" required checked={ack} onChange={event => setAck(event.target.checked)} />I have read the privacy notice. This does not enable location or photo sharing.</label>
      <Link href="/privacy">Read JOMO’s privacy notice</Link>
      <div className="j-row"><button className="j-button" disabled={action.pending || !ack}>Save and begin</button><button className="j-button secondary" type="button" onClick={() => setClosed(true)}>Remind me later</button></div><Feedback action={action} />
    </form>
  </Panel>;
}
