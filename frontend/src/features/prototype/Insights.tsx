"use client";
import { useCallback, useState } from "react";
import Link from "next/link";
import { TodayOverview } from "./TodayOverview";
import { request, usage, record, preferences, coach, success, z, minutes, localDate } from "@/services/prototype";
import { useResource, useAction, Feedback, ResourceState, Panel, Heading, Empty, Submit } from "./ui";

function CoachRecommendation() {
  const load = useCallback(() => request(coach, "/ai/wellbeing/recommendation", "post", {}), []);
  const view = useResource(load);
  return <Panel title="A gentle nudge">{view.data ? <p>{view.data.suggestion}</p> : <p>{view.error ? "Suggestions are unavailable. Your recorded data is still available." : "Gathering a suggestion…"}</p>}<Link href="/activities">Explore an offline activity</Link></Panel>;
}

export default function Insights() {
  const [period, setPeriod] = useState("7");
  const [saved, setSaved] = useState<z.infer<typeof record> | null>(null);
  const load = useCallback(async () => {
    const prefs = await request(preferences, "/users/me/preferences");
    const today = localDate(prefs.timezone);
    const end = period === "saved" && saved ? saved.usage_date : today;
    const start = new Date(`${end}T12:00:00Z`);
    start.setUTCDate(start.getUTCDate() - (period === "saved" ? 0 : Number(period) - 1));
    const summary = await request(usage, `/insights/summary?from=${start.toISOString().slice(0, 10)}&to=${end}`);
    return { summary, prefs };
  }, [period, saved]);
  const view = useResource(load);
  const action = useAction();
  return <>
    <TodayOverview />
    <section className="j-insights-details" aria-label="Screen-time records">
      <Heading level={2} eyebrow="Screen time · manually recorded" title="Your screen time, clearly recorded.">
        <p>This is separate from the offline activity totals above. Web JOMO does not automatically read other apps.</p>
      </Heading>
      <div className="j-row"><a className="j-button" href="#screen-time-form">Log screen time</a>
        <label>History <select className="j-select" value={period} onChange={event => setPeriod(event.target.value)}>
          <option value="7">Last 7 days</option><option value="30">Last 30 days</option>
          {saved && <option value="saved">Last saved date</option>}
        </select></label><button className="j-button secondary" onClick={view.refresh}>Refresh Insights</button></div>
      {view.error && <p className="j-error" role="alert">{saved ? "Your entry was saved, but Insights could not refresh." : view.error} <button onClick={view.refresh}>Try again</button></p>}
      {!view.data ? <ResourceState loading={view.loading} error={view.error} retry={view.refresh} /> : (() => {
        const { summary, prefs } = view.data;
        const today = localDate(prefs.timezone);
        const todayEntry = summary.daily_breakdown.find(row => row.usage_date === today);
        const largest = Math.max(1, ...summary.daily_breakdown.map(row => row.total_minutes));
        const categories: Record<string, number> = {};
        summary.daily_breakdown.forEach(row => Object.entries(row.category_breakdown ?? {}).forEach(([key, value]) => { categories[key] = (categories[key] ?? 0) + value; }));
        return <>
          <div className="j-grid">
            <Panel title="Screen time today"><strong className="j-stat">{todayEntry ? minutes(todayEntry.total_minutes) : "Not recorded in this view"}</strong><small>{today} · {prefs.timezone}</small></Panel>
            <Panel title="Average on recorded days"><strong className="j-stat">{summary.days_recorded ? minutes(summary.daily_average_minutes) : "Not recorded"}</strong><small>{summary.days_recorded} recorded days; missing days are not counted as zero.</small></Panel>
            <Panel title="Daily screen-time intention"><strong className="j-stat">{prefs.daily_screen_goal_minutes ? minutes(prefs.daily_screen_goal_minutes) : "Not set"}</strong>
              {todayEntry && prefs.daily_screen_goal_minutes && <p>{todayEntry.total_minutes <= prefs.daily_screen_goal_minutes ? "Within your intention today." : "Above your intention today. A fresh moment is always available."}</p>}<Link href="/settings">Adjust your intention</Link></Panel>
          </div>
          <Panel title="Recorded screen-time history">
            <p>{summary.start_date} to {summary.end_date}. Manual corrections take precedence over other sources for the same date.</p>
            {!summary.days_recorded ? <Empty>No screen time recorded in this window.</Empty> : <>
              <div className="j-bars" aria-hidden="true">{summary.daily_breakdown.map(row => <div className="j-bar" key={row.id}><span>{minutes(row.total_minutes)}</span><div style={{ height: `${140 * row.total_minutes / largest}px` }} /><span>{row.usage_date.slice(5)}</span></div>)}</div>
              <div className="j-table-wrap"><table><caption>Recorded screen time and source</caption><thead><tr><th>Date</th><th>Total</th><th>Social (included)</th><th>Source</th><th>Actions</th></tr></thead>
                <tbody>{summary.daily_breakdown.map(row => <tr key={row.id} className={row.id === saved?.id ? "j-saved-row" : undefined}>
                  <td>{row.usage_date}</td><td>{minutes(row.total_minutes)}</td><td>{row.social_minutes == null ? "Not supplied" : minutes(row.social_minutes)}</td><td>{row.source === "manual" ? "Manually entered" : row.source}</td>
                  <td>{row.source === "manual" && <><a href="#screen-time-form" onClick={() => setSaved(row)}>Edit</a> <button disabled={action.pending} onClick={() => {
                    if (!window.confirm(`Delete your screen-time entry for ${row.usage_date}?`)) return;
                    void action.run(async () => { await request(success, `/insights/records/${row.id}`, "delete"); setSaved(null); view.refresh(); }, "Screen-time entry deleted.");
                  }}>Delete</button></>}</td></tr>)}</tbody></table></div></>}
            <Feedback action={action} />
          </Panel>
          <div className="j-two"><CoachRecommendation key={summary.total_screen_time_minutes} /><Panel title="Entered categories">{Object.keys(categories).length ? Object.entries(categories).map(([key, value]) => <p key={key}>{key}: {minutes(value)}</p>) : <p>No breakdown supplied.</p>}<small>Based on entered values, not automatic app tracking.</small></Panel></div>
          <ScreenTimeForm key={`${prefs.timezone}:${saved?.id ?? "new"}`} timezone={prefs.timezone} initial={saved}
            onSave={row => { setSaved(row); view.refresh(); }} />
        </>;
      })()}
      {saved && <p className="j-notice" role="status">Saved {minutes(saved.total_minutes)} for {saved.usage_date}{saved.social_minutes != null ? `, including ${minutes(saved.social_minutes)} of social use` : ""}. <button onClick={() => setPeriod("saved")}>Show this date</button></p>}
    </section>
  </>;
}

function ScreenTimeForm({ timezone, initial, onSave }: { timezone: string; initial: z.infer<typeof record> | null; onSave: (row: z.infer<typeof record>) => void }) {
  const action = useAction();
  const [date, setDate] = useState(() => initial?.usage_date ?? localDate(timezone));
  const [hours, setHours] = useState(String(Math.floor((initial?.total_minutes ?? 0) / 60)));
  const [mins, setMins] = useState(String((initial?.total_minutes ?? 0) % 60));
  const [socialHours, setSocialHours] = useState(initial?.social_minutes != null ? String(Math.floor(initial.social_minutes / 60)) : "");
  const [socialMins, setSocialMins] = useState(initial?.social_minutes != null ? String(initial.social_minutes % 60) : "");
  const part = z.coerce.number().int().min(0);
  return <div id="screen-time-form"><Panel title={initial?.usage_date === date ? "Update screen time" : "Log screen time"}>
    <p>Copy your daily totals from your device’s Screen Time or Digital Wellbeing report. Social time is part of the total. This does not award coins or add offline minutes.</p>
    <form className="j-form" onSubmit={event => { event.preventDefault(); void action.run(async () => {
      const total = part.max(24).parse(hours) * 60 + part.max(59).parse(mins);
      const social = socialHours === "" && socialMins === "" ? null : part.max(24).parse(socialHours) * 60 + part.max(59).parse(socialMins);
      if (total > 1440 || (social != null && social > total)) throw new Error("Use up to 24 hours total, with social time no greater than the total.");
      const row = await request(record, "/insights/manual", "post", { usage_date: date, total_minutes: total, social_minutes: social, source: "manual" });
      onSave(row);
    }, "Screen time saved. Insights are refreshing."); }}>
      <label>Date ({timezone})<input type="date" required max={localDate(timezone)} value={date} onChange={event => setDate(event.target.value)} /></label>
      <div className="j-row"><label>Total hours<input type="number" required min={0} max={24} value={hours} onChange={event => setHours(event.target.value)} /></label><label>Total minutes<input type="number" required min={0} max={59} value={mins} onChange={event => setMins(event.target.value)} /></label></div>
      <div className="j-row"><label>Social hours (optional)<input type="number" min={0} max={24} value={socialHours} onChange={event => setSocialHours(event.target.value)} /></label><label>Social minutes (optional)<input type="number" min={0} max={59} value={socialMins} onChange={event => setSocialMins(event.target.value)} /></label></div>
      <small>Saving a date already recorded manually replaces that date’s manual values; it does not add them together.</small>
      <Submit pending={action.pending}>Save screen time</Submit><Feedback action={action} />
    </form>
  </Panel></div>;
}
