"use client";
import { useState } from "react";
import Link from "next/link";
import { TodayOverview } from "./TodayOverview";
import {
  request,
  usage,
  record,
  preferences,
  coach,
  z,
  minutes,
  localDate,
} from "@/services/prototype";
import {
  useResource,
  useAction,
  Feedback,
  ResourceState,
  Panel,
  Heading,
  Empty,
  Submit,
} from "./ui";
async function load() {
  const [summary, prefs] = await Promise.all([
    request(usage, "/insights/summary"),
    request(preferences, "/users/me/preferences"),
  ]);
  const recommendation = summary.days_recorded
    ? await request(coach, "/ai/wellbeing/recommendation", "post", {}).catch(
        () => null,
      )
    : null;
  return { summary, prefs, recommendation };
}
const manualForm = z
  .object({
    usage_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    total_minutes: z.coerce.number().int().min(0).max(1440),
    social_minutes: z.coerce.number().int().min(0).max(1440),
  })
  .refine(
    (value) => value.social_minutes <= value.total_minutes,
    "Social minutes cannot exceed total minutes.",
  );
export default function Insights() {
  const view = useResource(load),
    action = useAction();
  const [date, setDate] = useState(localDate),
    [total, setTotal] = useState("120"),
    [social, setSocial] = useState("30");
  if (!view.data)
    return (
      <ResourceState
        loading={view.loading}
        error={view.error}
        retry={view.refresh}
      />
    );
  const { summary, prefs, recommendation } = view.data;
  const goal = prefs.daily_screen_goal_minutes;
  const today = summary.daily_breakdown.filter(
    (row) => row.usage_date === localDate(),
  );
  const todayMinutes = today.reduce((sum, row) => sum + row.total_minutes, 0);
  const sources = [
    ...new Set(summary.daily_breakdown.map((row) => row.source)),
  ];
  const categories: Record<string, number> = {};
  for (const row of summary.daily_breakdown)
    for (const [key, value] of Object.entries(row.category_breakdown ?? {}))
      categories[key] = (categories[key] ?? 0) + value;
  const max = Math.max(
    1,
    ...summary.daily_breakdown.map((row) => row.total_minutes),
  );
  return (
    <>
      <TodayOverview />
      <div className="j-insights-details">
        <Heading
          level={2}
          eyebrow="A little perspective"
          title="Your digital habits, gently understood."
        >
          <p>
            Your digital habits, with a little perspective. Every small offline
            moment counts.
          </p>
        </Heading>
        <p>
          <span className="j-tag">
            Sources: {sources.length ? sources.join(", ") : "No records yet"}
          </span>
        </p>
        <p>
          <small>
            Web JOMO cannot read device-wide app usage. Manual, imported and
            imported records are labeled. Missing days are not counted as zero.
          </small>
        </p>
        <div className="j-grid">
          <Panel title="Today">
            <strong className="j-stat">
              {today.length ? minutes(todayMinutes) : "Not recorded"}
            </strong>
            <small>{localDate()}</small>
          </Panel>
          <Panel title="Recorded daily average">
            <strong className="j-stat">
              {summary.days_recorded
                ? minutes(summary.daily_average_minutes)
                : "—"}
            </strong>
            <small>
              {summary.start_date} to {summary.end_date} ·{" "}
              {summary.days_recorded} records
            </small>
          </Panel>
          <Panel title="Your daily intention">
            <strong className="j-stat">
              {goal ? minutes(goal) : "Set a goal"}
            </strong>
            {goal && today.length > 0 && (
              <>
                <progress
                  aria-label="Recorded screen time relative to goal"
                  max={goal}
                  value={Math.min(goal, todayMinutes)}
                />
                <p>
                  {todayMinutes <= goal
                    ? `${goal - todayMinutes} minutes within your intention.`
                    : "A fresh moment is always available."}
                </p>
              </>
            )}
            <Link href="/settings">Adjust your intention →</Link>
          </Panel>
        </div>
        <div className="j-two">
          <Panel title="Your week, at a glance">
            {!summary.days_recorded ? (
              <Empty>No usage recorded. Add your own entry below.</Empty>
            ) : (
              <>
                <div className="j-bars" aria-hidden="true">
                  {summary.daily_breakdown.map((row) => (
                    <div className="j-bar" key={row.id}>
                      <span>{minutes(row.total_minutes)}</span>
                      <div
                        style={{
                          height: `${(140 * row.total_minutes) / max}px`,
                        }}
                      />
                      <span>{row.usage_date.slice(5)}</span>
                    </div>
                  ))}
                </div>
                <div className="j-table-wrap">
                  <table>
                    <caption>Recorded usage and source</caption>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Total</th>
                        <th>Social</th>
                        <th>Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.daily_breakdown.map((row) => (
                        <tr key={row.id}>
                          <td>{row.usage_date}</td>
                          <td>{minutes(row.total_minutes)}</td>
                          <td>
                            {row.social_minutes == null
                              ? "Not supplied"
                              : minutes(row.social_minutes)}
                          </td>
                          <td>{row.source}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            <p>
              <small>
                Choose a single source for each date to keep your recorded
                averages clear.
              </small>
            </p>
          </Panel>
          <div>
            <Panel title="A gentle nudge">
              {recommendation ? (
                <>
                  <p>{recommendation.suggestion}</p>
                  <Link href="/activities">Make a little space →</Link>
                </>
              ) : (
                <p>
                  {summary.days_recorded
                    ? "Coach is unavailable. You can still explore offline activities."
                    : "Add usage before asking the coach for perspective."}
                </p>
              )}
            </Panel>
            <Panel title="Categories">
              {Object.keys(categories).length ? (
                Object.entries(categories).map(([key, value]) => (
                  <p className="j-spread" key={key}>
                    <span>{key}</span>
                    <strong>{minutes(value)}</strong>
                  </p>
                ))
              ) : (
                <Empty>No category breakdown supplied.</Empty>
              )}
              <small>Recorded categories, not inferred app telemetry.</small>
            </Panel>
          </div>
        </div>
        <Panel title="Add a manual check-in">
          <form
            className="j-form"
            onSubmit={(event) => {
              event.preventDefault();
              void action.run(async () => {
                const payload = manualForm.parse({
                  usage_date: date,
                  total_minutes: total,
                  social_minutes: social,
                });
                await request(record, "/insights/manual", "post", {
                  ...payload,
                  source: "manual",
                });
                view.refresh();
              }, "Manual usage saved.");
            }}
          >
            <label>
              Date
              <input
                type="date"
                required
                value={date}
                max={localDate()}
                onChange={(event) => setDate(event.target.value)}
              />
            </label>
            <label>
              Total minutes
              <input
                type="number"
                min="0"
                max="1440"
                required
                value={total}
                onChange={(event) => setTotal(event.target.value)}
              />
            </label>
            <label>
              Social minutes
              <input
                type="number"
                min="0"
                max="1440"
                required
                value={social}
                onChange={(event) => setSocial(event.target.value)}
              />
            </label>
            <Submit pending={action.pending}>Save manual entry</Submit>
          </form>
          <Feedback action={action} />
        </Panel>
      </div>
    </>
  );
}
