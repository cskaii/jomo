import type { Activity, ActivityParticipant } from "@/types/activity";

export interface OfflineRecord { id: string; title: string; category: string; minutes: number; date: string; groupId?: string | null }

// Planned duration and focus timers never count as completed offline time.
export function participationRecords(activities: Activity[], participants: ActivityParticipant[][], userId: string, timezone?: string): OfflineRecord[] {
  return activities.flatMap((item, index) => {
    const mine = participants[index]?.find((person) => person.user_id === userId);
    const stamp = mine?.completed_at ?? mine?.ended_at;
    if (!mine || mine.status !== "completed" || mine.eligible_minutes <= 0 || !stamp) return [];
    const normalized = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(stamp) ? stamp : `${stamp}Z`;
    const date = new Date(normalized);
    if (!Number.isFinite(date.getTime())) return [];
    const key = timezone ? new Intl.DateTimeFormat("en-CA", { timeZone: timezone, year: "numeric", month: "2-digit", day: "2-digit" }).format(date) : `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    return [{ id: item.id, title: item.title, category: item.category, minutes: mine.eligible_minutes, date: key, groupId: item.group_id }];
  }).sort((a, b) => b.date.localeCompare(a.date));
}

export function offlineStats(records: OfflineRecord[], today: string) {
  const key = (date: Date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  const days = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(`${today}T12:00:00`); date.setDate(date.getDate() - 6 + index);
    const day = key(date);
    return { date: day, label: date.toLocaleDateString("en", { weekday: "short" }), minutes: records.filter((record) => record.date === day).reduce((sum, record) => sum + record.minutes, 0) };
  });
  const week = records.filter((record) => days.some((day) => day.date === record.date));
  const dates = new Set(records.map((record) => record.date));
  const cursor = new Date(`${today}T12:00:00`);
  if (!dates.has(today)) cursor.setDate(cursor.getDate() - 1);
  let streak = 0;
  while (dates.has(key(cursor))) { streak += 1; cursor.setDate(cursor.getDate() - 1); }
  return { days, todayMinutes: days[6].minutes, weekCount: week.length, weekMinutes: week.reduce((sum, record) => sum + record.minutes, 0), streak };
}
