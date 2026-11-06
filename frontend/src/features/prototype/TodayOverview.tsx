"use client";
import Link from "next/link";
import { Footprints, ArrowUpRight, Leaf } from "lucide-react";
import { loadOfflineOverview } from "@/services/offline";
import { offlineStats } from "@/lib/offline";
import { localDate } from "@/services/prototype";
import { useResource } from "./ui";
import { PlanActivityDialog } from "./PlanActivityDialog";

export function TodayOverview() {
  const view = useResource(loadOfflineOverview);
  const stats = view.data ? offlineStats(view.data.records, localDate()) : null;
  const intention = 60,
    progress = stats
      ? Math.min(100, Math.round((stats.todayMinutes / intention) * 100))
      : 0;
  const max = Math.max(60, ...(stats?.days.map((day) => day.minutes) ?? []));
  return (
    <section className="j-today-hero" aria-label="Your offline day">
      <div className="j-today-inner">
        <div className="j-today-title">
          <div>
            <p className="j-eyebrow">
              {new Date().toLocaleDateString("en", {
                weekday: "long",
                day: "numeric",
                month: "long",
              })}
            </p>
            <h1>Today, you’re growing something.</h1>
          </div>
          <PlanActivityDialog />
        </div>
        {view.error && (
          <p className="j-error" role="alert">
            Your offline history is unavailable.{" "}
            <button onClick={view.refresh}>Try again</button>
          </p>
        )}
        <div className="j-today-stats" aria-busy={view.loading}>
          <section className="j-metric-card j-metric-ring">
            <div>
              <p className="j-eyebrow">Offline today</p>
              <strong>
                {stats ? stats.todayMinutes : "—"}
                <small> min</small>
              </strong>
              <p className="j-metric-caption">
                A gentle {intention}-minute intention.
                <br />
                {stats
                  ? `${Math.max(0, intention - stats.todayMinutes)} min to make a little more room`
                  : "Gathering your completed moments…"}
              </p>
            </div>
            <div
              className="j-progress-dial"
              style={{ "--progress": `${progress}%` } as React.CSSProperties}
            >
              <span>{stats ? `${progress}%` : "—"}</span>
            </div>
          </section>
          <section className="j-metric-card">
            <p className="j-eyebrow">Completed activities · 7d</p>
            <strong>{stats ? stats.weekCount : "—"}</strong>
            <div className="j-tick-track" aria-hidden="true">
              <span
                style={{
                  width: `${Math.min(100, (stats?.weekCount ?? 0) * 10)}%`,
                }}
              />
            </div>
            <p className="j-metric-caption">Small moments, adding up.</p>
          </section>
          <section className="j-metric-card">
            <p className="j-eyebrow">Current rhythm</p>
            <strong>
              {stats ? stats.streak : "—"}
              <small> {stats?.streak === 1 ? "day" : "days"}</small>
            </strong>
            <div className="j-tick-track" aria-hidden="true">
              <span
                style={{
                  width: `${Math.min(100, ((stats?.streak ?? 0) / 7) * 100)}%`,
                }}
              />
            </div>
            <p className="j-metric-caption">
              A rhythm, not a debt. Begin again anytime.
            </p>
          </section>
        </div>
        <div className="j-offline-grid">
          <section className="j-panel j-offline-chart">
            <div className="j-spread">
              <h2>
                Offline time <span>(7d)</span>
              </h2>
              <span className="j-mono">
                {stats
                  ? `${Math.round(stats.weekMinutes / 7)} min / day`
                  : "Not loaded"}
              </span>
            </div>
            <div
              className="j-week-chart"
              role="img"
              aria-label={
                stats
                  ? stats.days
                      .map((day) => `${day.label}: ${day.minutes} minutes`)
                      .join(", ")
                  : "Loading offline time"
              }
            >
              <div
                className="j-chart-goal"
                style={{ bottom: `${(60 / max) * 78 + 10}%` }}
              >
                <span>Intention 60</span>
              </div>
              {stats?.days.map((day) => (
                <div className="j-week-day" key={day.date}>
                  <div className="j-week-bar-wrap">
                    <div
                      className="j-week-bar"
                      style={{ height: `${(day.minutes / max) * 100}%` }}
                    >
                      {day.minutes > 0 && <span>{day.minutes}</span>}
                    </div>
                  </div>
                  <span>{day.label}</span>
                </div>
              ))}
              {!stats && (
                <p className="j-chart-empty" role="status">
                  {view.error
                    ? "Offline history unavailable"
                    : "Gathering your moments…"}
                </p>
              )}
            </div>
            {stats && !stats.weekCount && (
              <p className="j-chart-note">
                Your completed moments will take root here.{" "}
                <Link href="/activities">Plan your first →</Link>
              </p>
            )}
          </section>
          <section className="j-panel j-recent-panel">
            <div className="j-spread">
              <h2>Recent</h2>
              <Link
                className="j-icon-button"
                href="/activities"
                aria-label="All activities"
              >
                <ArrowUpRight aria-hidden="true" />
              </Link>
            </div>
            {view.data?.records.length ? (
              <div className="j-moment-list">
                {view.data.records.slice(0, 4).map((record) => (
                  <Link
                    className="j-moment"
                    key={record.id}
                    href={`/activities/${record.id}`}
                  >
                    <span className="j-soft-icon">
                      <Footprints aria-hidden="true" />
                    </span>
                    <div>
                      <strong>{record.title}</strong>
                      <small>
                        {record.category} · {record.minutes} min ·{" "}
                        {record.date.slice(5)}
                      </small>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="j-recent-empty">
                <Leaf aria-hidden="true" />
                <h3>Leave a little story.</h3>
                <p>
                  A walk. A book. An unhurried meal.
                  <br />
                  Your completed moments will appear here.
                </p>
                <Link href="/activities">Find your next moment →</Link>
              </div>
            )}
            <p className="j-panel-footnote">
              Recorded completed participation, not estimated time away.
            </p>
          </section>
        </div>
      </div>
    </section>
  );
}
